#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from xtsv import build_pipeline, parser_skeleton, jnius_config


def main():

    argparser = parser_skeleton(description='emstanzadep')
    argparser.add_argument('--naming-convention', dest='naming_convention', type=str, default='stanza',
                           help='Specify naming convention for output, can be `stanza` or `magyarlanc` (default: `stanza`)')
    opts = argparser.parse_args()

    jnius_config.classpath_show_warning = opts.verbose  # Suppress warning.

    # Set input and output iterators...
    if opts.input_text is not None:
        input_data = opts.input_text
    else:
        input_data = opts.input_stream
    output_iterator = opts.output_stream

    # Set the tagger name as in the tools dictionary
    used_tools = ['stanzadep']
    presets = []

    # Init and run the module as it were in xtsv

    # The relevant part of config.py
    # from emdummy import EmDummy
    em_stanzadep = ('emstanzadep', 'EmStanzaDep', 'Dependency parsing with Stanza',
                    (opts.naming_convention,), {'source_fields': {'form', 'lemma', 'upostag', 'feats'},  # Source field names
                                                'target_fields': ['id', 'deprel', 'head']})  # Target field names
    tools = [(em_stanzadep, ('emstanzadep', 'stanzadep', 'emStanzaDep'))]

    # Run the pipeline on input and write result to the output...
    output_iterator.writelines(build_pipeline(input_data, used_tools, tools, presets, opts.conllu_comments))

    # TODO this method is recommended when debugging the tool
    # Alternative: Run specific tool for input (still in emtsv format):
    # from xtsv import process
    # from emstanzadep import EmStanzaDep

    # proc = process(input_data, EmStanzaDep(*em_dummy[3], **em_dummy[4]))
    # output_iterator.writelines(proc)

    # Alternative2: Run REST API debug server
    # from xtsv import pipeline_rest_api, singleton_store_factory
    # app = pipeline_rest_api('TEST', tools, {},  conll_comments=False, singleton_store=singleton_store_factory(),
    #                         form_title='TEST TITLE', doc_link='https://github.com/dlt-rilmta/emdummy')
    # app.run()


if __name__ == '__main__':
    main()
