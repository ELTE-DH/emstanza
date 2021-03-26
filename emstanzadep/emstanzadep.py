#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import stanza
from stanza.models.common.doc import Document
import os


class EmStanzaDep:
    """
    Class to handle dependency parsing.
    """
    class_path = ''
    vm_opts = ''
    pass_header = True
    fixed_order_tsv_input = False

    def __init__(self, naming_convention, model_path=os.path.join(os.path.dirname(__file__), 'stanza_models'), source_fields=None, target_fields=None):
        """
        The initialisation of the module. One can extend the list of parameters as needed. The mandatory fields which
         should be set by keywords are the following:
        :param source_fields: the set of names of the input fields
        :param target_fields: the list of names of the output fields in generation order
        """
        # Custom code goes here

        # Field names for xtsv (the code below is mandatory for an xtsv module)
        if source_fields is None:
            source_fields = set()

        if target_fields is None:
            target_fields = []

        self.source_fields = source_fields
        self.target_fields = target_fields

        # This downloads the model, but we are packaging a frozen stanza model.
        # stanza.download(lang='hu', model_dir='./stanza_models', verbose=True, processors='depparse')

        self.stanza_depparse = stanza.Pipeline(lang='hu', dir=model_path, processors='depparse', depparse_pretagged=True, verbose=False)
        self.naming_convention = naming_convention

        if self.naming_convention == 'stanza':
            self.convert = self._to_stanza
        elif self.naming_convention == 'magyarlanc':
            self.convert = self._to_lanc
        else:
            raise NotImplementedError('Naming convention can either be `stanza` or `magyarlanc`.')

    def process_sentence(self, sen, field_names):
        """
        Process one sentence per function call
        :param sen: the list of all tokens in the sentence, each token contain all fields
        :param field_names: the prepared field_names from prepare_fields() to select the appropriate input field
         to process
        :return: the sen object augmented with the output field values for each token
        """
        # convert from xtsv to stanza
        stanza_sentence = []
        for i, line in enumerate(sen, start=1):
            stanza_sentence.append({'id': i, 'text': line[field_names['form']], 'lemma': line[field_names['lemma']],
                                    'upos': line[field_names['upostag']], 'feats': line[field_names['feats']]})

        # process with stanza
        # we convert from List[List[Dictionary]] to stanza Document and then back
        depparsed_sentence = self.stanza_depparse(Document([stanza_sentence])).to_dict()

        # merging depparsed sentence to original sentence inplace
        self.convert(sen, depparsed_sentence)

        return sen

    def _to_stanza(self, sen, depparsed_sentence):
        for parse, line in zip(depparsed_sentence[0], sen):
            # we are modifying the elements of sen inplace
            line += [str(parse['id']), parse['deprel'], str(parse['head'])]

    def _to_lanc(self, sen, depparsed_sentence):
        for parse, line in zip(depparsed_sentence[0], sen):
            loc = parse['deprel'].find(':') + 1  # -1+1 if no `:`, otherwise the location of `:`
            line += [str(parse['id']), parse['deprel'][loc:].upper(), str(parse['head'])]
        # last punctiation mark's head is 0 in magyarlanc
        sen[-1][-1] = '0'

    def prepare_fields(self, field_names):
        """
        This function is called once before processing the input. It can be used to initialise field conversion classes
         to accomodate the current order of fields (eg. field to features)
        :param field_names: the dictionary of the names of the input fields mapped to their order in the input stream
        :return: the list of the initialised feature classes as required for process_sentence (in most cases the
         columnnumbers of the required field in the required order are sufficient
         eg. return [field_names['form'], field_names['lemma'], field_names['xpostag'], ...] )
        """
        return field_names                           # TODO: Implement or overload on inherit

    def process_token(self, token):  # TODO implement or omit
        """
        This function is called when the REST API is called in 'one word mode' eg. GET /stem/this_word .
        It is not mandatory. If not present but sill called by the REST API an exception is raised.
        See EmMorphPy or HunspellPy for implementation example

        :param token: The input token
        :return: the processed output of the token preferably raw string or JSON string
        """
        return token
