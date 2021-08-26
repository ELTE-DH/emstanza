#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
from stanza import Pipeline
from stanza.models.common.doc import Document
from typing import List, Union


class EmStanza:
    """xtsv interface for Stanza"""

    class_path = ''
    vm_opts = ''
    pass_header = True
    fixed_order_tsv_input = False

    def __init__(self, task, model_path=os.path.join(os.path.dirname(__file__), 'stanza_models'),
                 source_fields=None, target_fields=None):
        """
        The initialisation of the module. One can extend the list of parameters as needed. The mandatory fields which
         should be set by keywords are source_fields and target_fields
        :param task: The name of the task (choice from available_tasks)
        :param model_path: The path of the Stanza model directory
        :param source_fields: The set of names of the input fields
        :param target_fields: The list of names of the output fields in generation order
        """

        available_tasks = {
            'tok': {
                'processors': 'tokenize',
                'encode_func': self._join_lines_ignore_hashmark,
                'decode_func': self._decode_stanza_tokenized,
                'pretokenized': False,
            },
            'tok-pos': {
                'processors': 'tokenize,pos',
                'encode_func': self._join_lines_ignore_hashmark,
                'decode_func': self._decode_stanza_tokenized,
                'pretokenized': False,
            },
            'tok-lem': {
                'processors': 'tokenize,pos,lemma',
                'encode_func': self._join_lines_ignore_hashmark,
                'decode_func': self._decode_stanza_tokenized,
                'pretokenized': False,
            },
            'tok-parse': {
                'processors': 'tokenize,pos,lemma,depparse',
                'encode_func': self._join_lines_ignore_hashmark,
                'decode_func': self._decode_stanza_tokenized,
                'pretokenized': False,
            },
            'parse': {
                'processors': 'depparse',
                'encode_func': self._encode_parse,
                'decode_func': self._decode_pretokenized,
                'pretokenized': False,
            },
            'pos': {
                'processors': 'tokenize,pos',
                'encode_func': self._encode_pretokenized,
                'decode_func': self._decode_pretokenized,
                'pretokenized': True,
            },
            'pos,lem': {
                'processors': 'tokenize,pos,lemma',
                'encode_func': self._encode_pretokenized,
                'decode_func': self._decode_pretokenized,
                'pretokenized': True,
            },
        }

        self.model_path = model_path

        setup_dict = available_tasks.get(task, None)
        if setup_dict is not None:
            self.pipeline = Pipeline(lang='hu', dir=self.model_path, processors=setup_dict['processors'], verbose=False,
                                     depparse_pretagged=setup_dict['processors'] == 'depparse',
                                     tokenize_pretokenized=setup_dict['pretokenized'])
            self._encode_sentence = setup_dict['encode_func']
            self._decode_sentence = setup_dict['decode_func']
        else:
            raise ValueError('No proper task is specified. The available tasks are {0}'.
                             format(' or '.join(available_tasks.keys())))

        self._task = task

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

        # xtsv -> stanza
        self.x2s_rosetta = {
            'id': 'id',
            'form': 'text',
            'lemma': 'lemma',
            'upostag': 'upos',
            'xpostag': 'xpos',
            'deprel': 'deprel',
            'head': 'head',
            'wsafter': 'wsafter',
            'feats': 'feats',
        }

        # Stanza -> xtsv (currently not in use)
        # self.s2x_rosetta = {v: k for k, v in self.x2s_rosetta}

        # This dictionary handles typecasting from stanza to xtsv (str)
        self.s2x_converter = {
            'id': str,
            'form': lambda s: s,
            'lemma': lambda s: s,
            'upostag': lambda s: s,
            'xpostag': lambda s: s or '_',
            'deprel': lambda s: s,
            'head': str,
            'wsafter': lambda s: s,
            'feats': lambda s: s or '_',
        }

    def _convert_fields_s2x(self, token):
        """Convert tields from Stanza to xtsv format"""

        return [self.s2x_converter[field](getattr(token.words[0], self.x2s_rosetta[field]))
                for field in self.target_fields]

    @staticmethod
    def _join_lines_ignore_hashmark(lines, *_) -> str:
        """Convert list of lines to string"""

        return ''.join(line for line in lines if not line.startswith('#'))

    @staticmethod
    def _encode_pretokenized(sen, field_names) -> str:
        """Convert to sentence-per-line form"""

        return ' '.join(tok[field_names['form']].strip() for tok in sen)

    def _decode_pretokenized(self, document, sen) -> Union[List[List[str]], List]:
        """
        Modifies xtsv-parsed sentence in-place by addig fields from the target_fields
        :param document: Stanza Document containing target_fields
        :param sen: List of lines in xtsv format
        :return: xtsv formatted sentence
        """

        for token, line in zip(document.sentences[0].tokens, sen):
            line += self._convert_fields_s2x(token)  # We are modifying the elements of sen inplace
        return sen

    @staticmethod
    def _encode_parse(sen, field_names) -> Document:
        """
        Converts from xtsv sentence to Stanza Document
        :param sen: An xtsv sentence
        :param field_names: Field names
        :return: Stanza Document containing one sentence
        """

        stanza_sentence = [{'id': i,
                            'text': line[field_names['form']],
                            'lemma': line[field_names['lemma']],
                            'upos': line[field_names['upostag']],
                            'feats': line[field_names['feats']],
                            } for i, line in enumerate(sen, start=1)]

        return Document([stanza_sentence])

    def _decode_stanza_tokenized(self, document: Document, *_) -> Union[List[List[str]], List]:
        """
        Decodes Documents if pipeline started from tokenization
        :param document: Stanza Document containing task-specific fields
        :return: Returns xtsv-formatted sentences
        """

        self._create_wsafter_field(document)

        for sentence in document.sentences:
            for token in sentence.tokens:
                yield '{0}\n'.format('\t'.join(self._convert_fields_s2x(token)))
            yield '\n'

    def _create_wsafter_field(self, document: Document):
        """
        Takes a stanza Document object and modifies it inplace by adding a .wsafter attribute for each token
        :param document: Stanza Document containing Tokens
        :return: None
        """

        last_sentence_idx = len(document.sentences)
        for sen_idx, sentence in enumerate(document.sentences, start=1):  # Document[Sentence[Token]]
            # Sentence DOES NOT contain trailing whitespaces, the information is only availabe on Document-level
            start_id = sentence.tokens[0].start_char
            for i in range(len(sentence.tokens) - 1):
                current_token, next_token = sentence.tokens[i: i + 2]
                # start_char and end_char are defined in relation to the original text
                #  also, I found no other way to convert to literal
                text_start = current_token.end_char - start_id
                text_end = next_token.start_char - start_id
                current_token.words[0].wsafter = self._whitespace_to_literal(sentence.text[text_start:text_end])

            # At the last token, we do things differently
            current_token = sentence.tokens[-1]
            text_start = current_token.end_char
            # We check if we are in the last sentence
            if sen_idx != last_sentence_idx:
                # If not, there is a next token in the document, else the whitespaces are at the end of the document
                next_token = document.sentences[sen_idx].tokens[0]
                text_end = next_token.start_char
                current_token.words[0].wsafter = self._whitespace_to_literal(document.text[text_start: text_end])
            else:
                current_token.words[0].wsafter = self._whitespace_to_literal(document.text[text_start:])

    @staticmethod
    def _whitespace_to_literal(text: str) -> str:
        """Escape whisespaces and wrap them with quotes"""

        return f'"{text.__repr__()[1:-1]}"'  # HACK

    def process_sentence(self, sen, field_names=None):
        """
        Process one sentence per function call
        :param sen: The list of all tokens in the sentence, each token contain all fields
        :param field_names: The prepared field_names from prepare_fields() to select the appropriate input field
         to process
        :return: The sen object augmented with the output field values for each token
        """

        # Encode to stanza format
        encoded_doc = self._encode_sentence(sen, field_names)

        # Process in Stanza and convert to List[List[Dict]] as in Document[Sentence[Token]]
        processed_doc = self.pipeline(encoded_doc)

        # Decode sentence to xtsv
        decoded_sen = self._decode_sentence(processed_doc, sen)

        yield from decoded_sen

    @staticmethod
    def prepare_fields(field_names):
        """
        This function is called once before processing the input. It can be used to initialise field conversion classes
         to accomodate the current order of fields (eg. field to features)
        :param field_names: The dictionary of the names of the input fields mapped to their order in the input stream
        :return: The list of the initialised feature classes as required for process_sentence (in most cases the
         columnnumbers of the required field in the required order are sufficient
         e.g. return [field_names['form'], field_names['lemma'], field_names['xpostag'], ...] )
        """
        return field_names
