#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from xtsv import build_pipeline, parser_skeleton, jnius_config


def main():

    argparser = parser_skeleton(description='emStanza - Stanza fitted to xtsv')
    argparser.add_argument('--task', dest='emstanza_task', required=True,
                           help='Task to do (tok, pos, lem, parse, tok-pos, tok-parse, etc.')
    opts = argparser.parse_args()

    jnius_config.classpath_show_warning = opts.verbose  # Suppress warning.

    # Set input and output iterators...
    if opts.input_text is not None:
        input_data = opts.input_text
    else:
        input_data = opts.input_stream
    output_iterator = opts.output_stream

    # Set the tagger name as in the tools dictionary
    used_tools = ['stanza']
    presets = []

    # Init and run the module as it were in xtsv

    # The relevant part of config.py
    # from emdummy import EmDummy

    available_tasks = {
        'tok': {'task': 'tok', 'source_fields': set(), 'target_fields': ['form', 'wsafter']},
        'tok-pos': {
            'task': 'tok-pos',
            'source_fields': set(),
            'target_fields': ['form', 'wsafter', 'feats', 'upostag', 'xpostag'],
        },
        'tok-lem': {
            'task': 'tok-lem',
            'source_fields': set(),
            'target_fields': ['form', 'wsafter', 'feats', 'upostag', 'xpostag', 'lemma'],
        },
        'tok-parse': {
            'task': 'tok-parse',
            'source_fields': set(),
            'target_fields': ['form', 'wsafter', 'feats', 'upostag', 'xpostag', 'lemma', 'id', 'deprel', 'head'],
        },
        'parse': {
            'task': 'parse',
            'source_fields': {'form', 'lemma', 'upostag', 'feats'},
            'target_fields': ['id', 'deprel', 'head'],
        },
        'pos': {
            'task': 'pos',
            'source_fields': {'form'},
            'target_fields': ['upostag', 'xpostag', 'feats']
        },
        'pos,lem': {
            'task': 'pos,lem',
            'source_fields': {'form'},
            'target_fields': ['upostag', 'xpostag', 'feats', 'lemma']
        }
    }

    if opts.emstanza_task not in available_tasks.keys():
        raise ValueError(f'task parameter must be one of {available_tasks.keys()} !')

    emstanza = (
        'emstanza',
        'EmStanza',
        'Processing with Stanza',
        (),
        available_tasks[opts.emstanza_task],
    )  # Target field names
    tools = [(emstanza, ('emstanza', 'stanza', 'emStanza'))]

    # Run the pipeline on input and write result to the output...
    output_iterator.writelines(build_pipeline(input_data, used_tools, tools, presets, opts.conllu_comments))

    # TODO this method is recommended when debugging the tool
    # Alternative: Run specific tool for input (still in emtsv format):
    # from xtsv import process
    # from emstanza import EmStanza

    # proc = process(input_data, EmStanza(*emstanza[3], **emstanza[4]))
    # output_iterator.writelines(proc)

    # For testing all of the tokenizer settings. Supply a text file and it will write to stdout all the tokenizer tasks.
    # from xtsv import process
    # from emstanza import EmStanza
    # from io import StringIO
    # input_text = ''.join(input_data)
    # for task_name, task in available_tasks.items():
    #     if task_name.startswith('tok'):
    #         emstanza = ('emstanza', 'EmStanza', 'Test', (), task)
    #         proc = process(StringIO(input_text), EmStanza(*emstanza[3], **emstanza[4]))
    #         output_iterator.writelines(proc)
    #     else:
    #         continue

    # Alternative2: Run REST API debug server
    # from xtsv import pipeline_rest_api, singleton_store_factory
    # app = pipeline_rest_api('TEST', tools, {},  conll_comments=False, singleton_store=singleton_store_factory(),
    #                         form_title='TEST TITLE', doc_link='https://github.com/dlt-rilmta/emdummy')
    # app.run()


if __name__ == '__main__':
    main()
