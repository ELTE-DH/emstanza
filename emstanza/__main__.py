#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from xtsv import build_pipeline, parser_skeleton, jnius_config


def main():

    argparser = parser_skeleton(description="emstanza")
    opts = argparser.parse_args()

    jnius_config.classpath_show_warning = opts.verbose  # Suppress warning.

    # Set input and output iterators...
    if opts.input_text is not None:
        input_data = opts.input_text
    else:
        input_data = opts.input_stream
    output_iterator = opts.output_stream

    # Set the tagger name as in the tools dictionary
    used_tools = ["stanza"]
    presets = []

    # Init and run the module as it were in xtsv

    # The relevant part of config.py
    # from emdummy import EmDummy

    available_tasks = {
        "tok": {"task": "tok", "source_fields": set(), "target_fields": ["form", "wsafter"]},
        "tok-pos": {"task": "tok-pos", "source_fields": set(), "target_fields": ["form", "wsafter", "feats", "upostag", "xpostag"]},
        "tok-lem": {"task": "tok-lem", "source_fields": set(), "target_fields": ["form", "wsafter", "feats", "upostag", "xpostag", "lemma"]},
        "tok-parse": {
            "task": "tok-parse",
            "source_fields": set(),
            "target_fields": ["form", "wsafter", "feats", "upostag", "xpostag", "lemma", "id", "deprel", "head"],
        },
        "parse": {
            "task": "parse",
            "source_fields": {'form', 'lemma', 'upostag', 'feats'},
            "target_fields": ["id", "deprel", "head"],
        },
    }

    emstanza = (
        "emstanza",
        "EmStanza",
        "Parsing with Stanza",
        (),
        available_tasks['tok-parse'],
    )  # Target field names
    # tools = [(emstanza, ("emstanza", "stanza", "emStanza"))]

    # Run the pipeline on input and write result to the output...
    # output_iterator.writelines(build_pipeline(input_data, used_tools, tools, presets, opts.conllu_comments))

    # TODO this method is recommended when debugging the tool
    # Alternative: Run specific tool for input (still in emtsv format):
    from xtsv import process
    from emstanza import EmStanza

    proc = process(input_data, EmStanza(*emstanza[3], **emstanza[4]))
    output_iterator.writelines(proc)

    # For testing all of the tokenizer settings. Supply a text file and it will write to stdout all the tokenizer tasks.
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


if __name__ == "__main__":
    main()
