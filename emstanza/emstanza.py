#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
from stanza import Pipeline
from stanza.models.common.doc import Document
from typing import List


class EmStanza:
    """
    Class to handle dependency parsing.
    """

    class_path = ''
    vm_opts = ''
    pass_header = True
    fixed_order_tsv_input = False

    def __init__(
        self,
        task,
        model_path=os.path.join(os.path.dirname(__file__), 'stanza_models'),
        source_fields=None,
        target_fields=None,
    ):
        """
        The initialisation of the module. One can extend the list of parameters as needed. The mandatory fields which
         should be set by keywords are the following:
        :param source_fields: the set of names of the input fields
        :param target_fields: the list of names of the output fields in generation order
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
            self._setup(**setup_dict)
        else:
            raise ValueError(
                'No proper task is specified. The available tasks are {0}'.format(' or '.join(available_tasks.keys()))
            )

        self._task = task

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

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

        # this dictionary handles typecasting from stanza to xtsv (str)
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

        # currently not in use
        self.s2x_rosetta = {
            'id': 'id',
            'text': 'form',
            'lemma': 'lemma',
            'upos': 'upostag',
            'xpos': 'xpostag',
            'deprel': 'deprel',
            'head': 'head',
            'wsafter': 'wsafter',
            'feats': 'feats',
        }

    def _setup(self, processors, encode_func, decode_func, pretokenized):

        depparse_pretagged = processors == 'depparse'
        self.pipeline = Pipeline(
            lang='hu',
            dir=self.model_path,
            processors=processors,
            verbose=False,
            depparse_pretagged=depparse_pretagged,
            tokenize_pretokenized=pretokenized,
        )
        self._encode_sentence = encode_func
        self._decode_sentence = decode_func

    @staticmethod
    def _join_lines_ignore_hashmark(lines, *_) -> str:
        return ''.join(line for line in lines if not line.startswith('#'))

    @staticmethod
    def _encode_pretokenized(sen, field_names) -> str:
        return ' '.join(tok[field_names['form']].strip() for tok in sen)

    def _decode_pretokenized(self, document, sen) -> List[List[str]]:
        """
        Modifies xtsv-parsed sentence in-place by addig fields from the target_fields.
        :param sen: list of lines in xtsv format
        :param document: Stanza Document containing target_fields.
        :return: xtsv formatted sentence.
        """

        for token, line in zip(document.sentences[0].tokens, sen):
            # we are modifying the elements of sen inplace
            line += [
                self.s2x_converter[field](getattr(token.words[0], self.x2s_rosetta[field]))
                for field in self.target_fields
            ]

        return sen

    @staticmethod
    def _encode_parse(sen, field_names) -> Document:
        """
        Converts from xtsv sentence to Stanza Document.
        :param sen: xtsv sentence
        :param field_names: field names
        :return: Stanza Document containing one sentence.
        """

        stanza_sentence = [
            {
                'id': i,
                'text': line[field_names['form']],
                'lemma': line[field_names['lemma']],
                'upos': line[field_names['upostag']],
                'feats': line[field_names['feats']],
            }
            for i, line in enumerate(sen, start=1)
        ]

        return Document([stanza_sentence])

    def _decode_stanza_tokenized(self, document: Document, *_) -> List[List[str]]:
        """
        Decodes Documents if pipeline started from tokenization.
        :param document: Stanza Document containing task-specific fields.
        :return: Returns xtsv-formatted sentences.
        """

        self._create_wsafter_field(document)

        xtsv_sentences = []
        for sentence in document.sentences:
            current_sentence = [
                [
                    self.s2x_converter[field](getattr(token.words[0], self.x2s_rosetta[field]))
                    for field in self.target_fields
                ]
                for token in sentence.tokens
            ]
            xtsv_sentences.append('{}\n\n'.format('\n'.join('\t'.join(line) for line in current_sentence)))

        return xtsv_sentences

    def _create_wsafter_field(self, document: Document):
        """
        Takes a stanza Document object and modifies it inplace by adding a .wsafter attribute.
        :param document: Stanza Document containing Tokens.
        :return: None.
        """

        for sen_idx, sentence in enumerate(document.sentences, start=1):  # Document[Sentence[Token]]
            # Sentence DOES NOT contain trailing whitespaces, the information is only availabe on Document-level
            start_id = sentence.tokens[0].start_char
            for i in range(0, len(sentence.tokens) - 1):
                current_token, next_token = sentence.tokens[i: i + 2]
                # start_char and end_char are defined in relation to the original text
                # also, I found no other way to convert to literal
                current_token.words[0].wsafter = self._convert_to_xtsv_literal(
                    sentence.text[current_token.end_char - start_id: next_token.start_char - start_id]
                )

            # at the last token, we do things differently
            current_token = sentence.tokens[-1]
            # we check if we are in the last sentence, if not, there is a next token in the document, else the whitespaces are at the end of the document
            if sen_idx != len(document.sentences):
                next_token = document.sentences[sen_idx].tokens[0]
                current_token.words[0].wsafter = self._convert_to_xtsv_literal(
                    document.text[current_token.end_char: next_token.start_char]
                )
            else:
                current_token.words[0].wsafter = self._convert_to_xtsv_literal(
                    document.text[current_token.end_char:]
                )

    @staticmethod
    def _convert_to_xtsv_literal(text: str) -> str:
        return '"' + text.__repr__().strip('\'') + '"'  # HACK

    def process_sentence(self, sen, field_names=None):
        """
        Process one sentence per function call
        :param sen: the list of all tokens in the sentence, each token contain all fields
        :param field_names: the prepared field_names from prepare_fields() to select the appropriate input field
         to process
        :return: the sen object augmented with the output field values for each token
        """

        # encode to stanza format
        encoded_doc = self._encode_sentence(sen, field_names)

        # process in stanza and convert to list[list[dict]] as in Document[Sentence[Token]]
        processed_doc = self.pipeline(encoded_doc)

        # decode sentence to xtsv
        decoded_sen = self._decode_sentence(processed_doc, sen)

        yield from decoded_sen

    @staticmethod
    def prepare_fields(field_names):
        """
        This function is called once before processing the input. It can be used to initialise field conversion classes
         to accomodate the current order of fields (eg. field to features)
        :param field_names: the dictionary of the names of the input fields mapped to their order in the input stream
        :return: the list of the initialised feature classes as required for process_sentence (in most cases the
         columnnumbers of the required field in the required order are sufficient
         eg. return [field_names['form'], field_names['lemma'], field_names['xpostag'], ...] )
        """
        return field_names  # TODO: Implement or overload on inherit
