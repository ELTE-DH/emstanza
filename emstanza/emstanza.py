#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from stanza.models.common.doc import Document
from stanza import Pipeline
import os


class EmStanza:
    """
    Class to handle dependency parsing.
    """

    class_path = ""
    vm_opts = ""
    pass_header = True
    fixed_order_tsv_input = False

    def __init__(self, task, model_path=os.path.join(os.path.dirname(__file__), "stanza_models"), source_fields=None, target_fields=None):
        """
        The initialisation of the module. One can extend the list of parameters as needed. The mandatory fields which
         should be set by keywords are the following:
        :param source_fields: the set of names of the input fields
        :param target_fields: the list of names of the output fields in generation order
        """
        # Custom code goes here

        # stanza.download(lang='hu', model_dir='./stanza_models', verbose=True)

        available_tasks = {
            "tok": self._setup_tok,
            "tok-pos": self._setup_tok_pos,
            "tok-lem": self._setup_tok_lem,
            "tok-parse": self._setup_tok_parse,
            "parse": self._setup_parse,
        }

        self.model_path = model_path

        setup_fun = available_tasks.get(task, None)
        if setup_fun is not None:
            setup_fun()
        else:
            raise ValueError("No proper task is specified. The available tasks are {0}".format(" or ".join(available_tasks.keys())))

        self._task = task

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

        # self.stanza_depparse = Pipeline(lang="hu", dir=model_path, processors="depparse", depparse_pretagged=True, verbose=False)

    def _setup_tok(self):
        self.pipeline = Pipeline(lang="hu", dir=self.model_path, processors="tokenize", verbose=False)
        self._encode_sentence = self._join_lines_ignore_hashmark
        self._decode_sentence = self._decode_sentence_tok

    def _setup_tok_pos(self):
        self.pipeline = Pipeline(lang="hu", dir=self.model_path, processors="tokenize,pos", verbose=False)
        self._encode_sentence = self._join_lines_ignore_hashmark
        self._decode_sentence = self._decode_sentence_tok_pos

    def _setup_tok_lem(self):
        self.pipeline = Pipeline(lang="hu", dir=self.model_path, processors="tokenize,pos,lemma", verbose=False)
        self._encode_sentence = self._join_lines_ignore_hashmark
        self._decode_sentence = self._decode_sentence_tok_lem

    def _setup_tok_parse(self):
        self.pipeline = Pipeline(lang="hu", dir=self.model_path, processors="tokenize,pos,lemma,depparse", verbose=False)
        self._encode_sentence = self._join_lines_ignore_hashmark
        self._decode_sentence = self._decode_sentence_tok_parse

    def _setup_parse(self):
        self.pipeline = Pipeline(lang="hu", dir=self.model_path, processors="depparse", verbose=False, depparse_pretagged=True)
        self._encode_sentence = self._encode_parse
        self._decode_sentence = self._decode_parse

    @staticmethod
    def _join_lines_ignore_hashmark(lines, field_names):
        return ''.join([line for line in lines if not line.startswith('#')])

    @staticmethod
    def _encode_parse(sen, field_names) -> Document:
        """
        Converts from xtsv sentence to Stanza Document.
        :param sen: xtsv sentence
        :param field_names: field names
        :return: Stanza Document containing one sentence.
        """
        stanza_sentence = []
        for i, line in enumerate(sen, start=1):
            stanza_sentence.append({'id': i, 'text': line[field_names['form']], 'lemma': line[field_names['lemma']],
                                    'upos': line[field_names['upostag']], 'feats': line[field_names['feats']]})

        return(Document([stanza_sentence]))

    @staticmethod
    def _decode_parse(document: Document, sen: list) -> list:
        """
        Modifies xtsv-parsed sentenced in-place by addig `id`, `deprel`, `head` fields.
        :param sen: list of lines in xtsv format
        :param document: Stanza Document containing depparse
        :return: None.
        """
        for token, line in zip(document.sentences[0].tokens, sen):
            # we are modifying the elements of sen inplace
            line += [str(token.words[0].id), token.words[0].deprel, str(token.words[0].head)]

        return(sen)

    def _decode_sentence_tok_parse(self, document: Document, *_) -> list:
        """
        Takes a stanza Document as argument and returns `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma` fields
        :param document: Stanza Document containing POS-tagged Tokens and wsafter.
        :return: xtsv formatted lines with `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma` fields
        """

        self._create_wsafter_field(document)

        xtsv_sentences = []

        for sentence in document.sentences:
            current_sentence = []
            for idx, token in enumerate(sentence.tokens):
                # feats is None if PUNCT
                current_sentence.append([token.text, token.wsafter, str(token.words[0].feats or '_'), token.words[0].upos, token.words[0].xpos or '_',
                                         token.words[0].lemma, str(token.words[0].id), token.words[0].deprel, str(token.words[0].head)])
            xtsv_sentences.append('\n'.join(['\t'.join(line) for line in current_sentence] + ['\n']))

        return(xtsv_sentences)

    def _decode_sentence_tok_lem(self, document: Document, *_) -> list:
        """
        Takes a stanza Document as argument and returns `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma` fields
        :param document: Stanza Document containing POS-tagged Tokens and wsafter.
        :return: xtsv formatted lines with `form`, `wsafter`, `feats`, `upostag`, `xpostag`, `lemma` fields
        """

        self._create_wsafter_field(document)
        xtsv_sentences = []

        for sentence in document.sentences:
            current_sentence = []
            for token in sentence.tokens:
                # feats is None if PUNCT
                current_sentence.append([token.text, token.wsafter, str(token.words[0].feats or '_'), token.words[0].upos,
                                         token.words[0].xpos or '_', token.words[0].lemma])
            xtsv_sentences.append('\n'.join(['\t'.join(line) for line in current_sentence] + ['\n']))

        return(xtsv_sentences)

    def _decode_sentence_tok_pos(self, document: Document, *_):
        """
        Takes a stanza Document as argument and returns `form`, `wsafter`, `feats`, `upostag`, `xpostag` fields
        :param document: Stanza Document containing POS-tagged Tokens and wsafter.
        :return: xtsv formatted text with `form`, `wsafter`, `feats`, `upostag`, `xpostag` fields
        """

        self._create_wsafter_field(document)

        xtsv_sentences = []

        for sentence in document.sentences:
            current_sentence = []
            for token in sentence.tokens:
                # feats is None if PUNCT
                current_sentence.append([token.text, token.wsafter, str(token.words[0].feats or '_'), token.words[0].upos, token.words[0].xpos or '_'])
            xtsv_sentences.append('\n'.join(['\t'.join(line) for line in current_sentence] + ['\n']))

        return(xtsv_sentences)

    def _decode_sentence_tok(self, document: Document, *_):
        """
        Takes a stanza Document as argument and returns `form`, `wsafter` fields
        :param document: Stanza Document containing Tokens and wsafter.
        :return: xtsv formatted text with `form`, `wsafter` fields.
        """

        self._create_wsafter_field(document)

        xtsv_sentences = []

        for sentence in document.sentences:
            current_sentence = []
            for token in sentence.tokens:
                # feats is None if PUNCT
                current_sentence.append([token.text, token.wsafter])
            xtsv_sentences.append('\n'.join(['\t'.join(line) for line in current_sentence] + ['\n']))

        return(xtsv_sentences)

    @staticmethod
    def _create_wsafter_field(document: Document):

        """
        Takes a stanza Document object and modifies it inplace by adding a .wsafter attribute.
        :param document: Stanza Document containing Tokens.
        :return: None.
        """

        for sen_idx, sentence in enumerate(document.sentences):  # Document[Sentence[Token]]
            # Sentence DOES NOT contain trailing whitespaces, the information is only availabe on Document-level
            start_id = sentence.tokens[0].start_char
            for i in range(0, len(sentence.tokens) - 1):
                current_token, next_token = sentence.tokens[i: i + 2]
                # start_char and end_char are defined in relation to the original text
                # also, I found no other way to convert to literal
                wsafter = sentence.text[current_token.end_char - start_id: next_token.start_char - start_id].__repr__().strip("'")  # HACK
                current_token.wsafter = f'"{wsafter}"'

            else:
                current_token = sentence.tokens[-1]
                # we check if we are in the last sentence, if not, there is a next token in the document, else the whitespaces are at the end of the document
                if sen_idx != len(document.sentences) - 1:
                    next_token = document.sentences[sen_idx + 1].tokens[0]
                    wsafter = document.text[current_token.end_char: next_token.start_char].__repr__().strip("'")
                else:
                    wsafter = document.text[current_token.end_char:].__repr__().strip("'")
                current_token.wsafter = f'"{wsafter}"'

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

    def prepare_fields(self, field_names):
        """
        This function is called once before processing the input. It can be used to initialise field conversion classes
         to accomodate the current order of fields (eg. field to features)
        :param field_names: the dictionary of the names of the input fields mapped to their order in the input stream
        :return: the list of the initialised feature classes as required for process_sentence (in most cases the
         columnnumbers of the required field in the required order are sufficient
         eg. return [field_names['form'], field_names['lemma'], field_names['xpostag'], ...] )
        """
        return field_names  # TODO: Implement or overload on inherit

    def process_token(self, token):  # TODO implement or omit
        """
        This function is called when the REST API is called in 'one word mode' eg. GET /stem/this_word .
        It is not mandatory. If not present but sill called by the REST API an exception is raised.
        See EmMorphPy or HunspellPy for implementation example

        :param token: The input token
        :return: the processed output of the token preferably raw string or JSON string
        """
        return token
