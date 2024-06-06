# Roc bindings generator

A helper script for generating part of the [language bindings](https://roc-streaming.org/toolkit/docs/api/bindings.html) (enums, config structs) for [Roc Toolkit](https://github.com/roc-streaming/roc-toolkit/).

Run with `--help` for more info.

```
usage: generate_bindings.py [-h] -t {all,java,go} [--toolkit_dir TOOLKIT_DIR] [--doxygen_dir DOXYGEN_DIR]
                            [--go_output_dir GO_OUTPUT_DIR] [--java_output_dir JAVA_OUTPUT_DIR]

Generate bindings

options:
  -h, --help            show this help message and exit
  -t {all,java,go}, --type {all,java,go}
                        Type of enum generation
  --toolkit_dir TOOLKIT_DIR
                        Roc Toolkit directory (default: ../roc-toolkit)
  --doxygen_dir DOXYGEN_DIR
                        Doxygen XML directory (default: <toolkit_dir>/build/docs/public_api/xml)
  --go_output_dir GO_OUTPUT_DIR
                        Go output directory (default: ../roc-go)
  --java_output_dir JAVA_OUTPUT_DIR
                        Java output directory (default: ../roc-java)
```
