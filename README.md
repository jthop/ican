[![build, publish, and release](https://github.com/jthop/ican/actions/workflows/build_pub_release.yml/badge.svg)](https://github.com/jthop/ican/actions/workflows/build_pub_release.yml)
[![CodeFactor](https://www.codefactor.io/repository/github/jthop/ican/badge)](https://www.codefactor.io/repository/github/jthop/ican)
[![PyPI version](https://badge.fury.io/py/ican.svg)](https://badge.fury.io/py/ican)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![GitHub last commit](https://img.shields.io/github/last-commit/jthop/flask-api-key)](https://github.com/jthop/flask-api-key)
[![GitHub repo size](https://img.shields.io/github/repo-size/jthop/flask-api-key?style=flat)](https://github.com/jthop/flask-api-key)
[![GitHub language count](https://img.shields.io/github/languages/count/jthop/flask-api-key?style=flat)](https://github.com/jthop/flask-api-key)
[![GitHub top language](https://img.shields.io/github/languages/top/jthop/flask-api-key?style=flat)](https://python.org)
[![Whos your daddy](https://img.shields.io/badge/whos%20your%20daddy-2.0.7rc3-brightgreen.svg)](https://14.do/)
[![works badge](https://cdn.jsdelivr.net/gh/nikku/works-on-my-machine@v0.2.0/badge.svg)](https://github.com/nikku/works-on-my-machine)


# :wave: ican

any deploy/build task you ask of it, the response is always: ican

```
can you bump my version to the next prerelease?
dev@macbook:~/proj$ ican 

can you use that version as a git tag and push a commit to the tag?
dev@macbook:~/proj$ ican 

can you deploy my new version by building a docker container and starting it?
dev@macbook:~/proj$ ican 
```

## :floppy_disk: Install

Install the ican package via pypi

```shell
pip install ican
```

## :toolbox: Sample Config

Config is done via the .ican file in your project's root diarectory.

Sample .ican config file

```ini
[version]
current = 0.1.6+build.40

[options]
log-file = ican.log

[file: version]
file = ./src/__init__.py
style = semantic
variable = __version__

[pipeline: release]
step1 = ./clean_my_project.sh
step2 = git commit -a
step3 = git tag -a {{tag}} --sign
step4 = git push origin master {{tag}}

```

### Sample config explanation

- This config defines the current version as `0.1.6` with build # 40.
- All operations will be logged to the `ican.log` file.
- ican will update a variable named `__version__` in `./src/__init__.py` any time the bump command is run.
  - ican will use the `semantic` style of the version when updating this file.
- The release pipeline will run on bump [patch, minor, or major].
  - This pipeline has 4 steps defined.
  - All pipeline steps are shell-based commands.

### Important
Take note, all sections must be unique.  So if you define more than one <file: [LABEL]> section, make sure each one has a unique label.

### :thumbsup: :sunglasses:
```ini
[file: src_init]
file = ./src/__init__.py
...
[file: main]
file = ./src/__main__.py
```

### :thumbsdown: :skull_and_crossbones:
```ini
[file: py_code]
file = ./src/__init__.py
...
[file: py_code]
file = ./src/__main__.py
```

## :triangular_ruler: Config

| Section          | Key             | Value                                           |
| -----------------| ----------------|-------------------------------------------------|
| version          | current         | This is the value that ican stores the current version number in. |
| options          | log-file        |All operations are logged to disk in this file.  To turn logging off, do not define the log-file. |
| file: [LABEL]    | file            | The filename of a file ican will update with new versions.  You can use a standard unix glob (*.py) if desired. |
| file: [LABEL]    | style           | The version style to use.  Choices are [semantic, public, pep440, git] |
| file: [LABEL]    | variable        | The variable name pointing to the version string that ican will update when versions are bumped. |
| file: [LABEL]    | regex           | User-supplied python formattted regex string defining how to replace the file's version. |
| pipeline: [LABEL]| stepN (step1...)| Pipeline step.  These represent a command run in the shell. |


### User-supplied regex

When looking for a variable, ican will look for any string followed by an `=` symbol, followed by a value in either single or double quotes.  There can be spaces or no spaces on either side of the `=` symbol.  This should cover most use cases.

If your use case is more complicated, you can omit the `variable` line in your config file and instead include a `regex` value instead.  This should be a pyton formatted regex string with a named group to identify the `version` ican will replace.


```ini
[file1]
file = ./src/__init__.py
style = semantic
regex = __version__\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)
```

## :muscle: Use

You can use ican via the CLI in a typical fashion, using the format below

```shell
ican [command] [arguments] [options] 
```

## :dog2: Commands

| Command      | Arguments             | Description   |
| -------------| --------------------  | ------------- |
| bump       | **PART** `required`     |The **PART** is the segment of the semantic version to increment.  <br />Choices are [*major*, *minor*, *patch*, *prerelease*] |
| show       | **STYLE** `required`    | The **STYLE** is the version format to show. <br />Choices are [*semantic*, *public*, *pep440*, *git*] |
| init       | none.                   | This command would initialize your project with default config in the current directory.                                |


## :roll_eyes: Options

The output and parsing of `ican` can be controlled with the following options.

| Name                   | Description                                                  |
| -------------          | -------------                                                |
| `--verbose`            | To aid in your debugging, verbose prints all messages.       |
| `--dry-run`            | Useful if used WITH --verbose, will not modify any files.    |
| `--version`            | This will displpay the current version of ican.              |
| `--canonical`          | Test if the pep440 version conforms to pypi's specs          |

## :eyes: Examples

```bash
$ ican init

...

$ ican show current
0.2.7-beta.3+build.99

# Lets run a build.  Bump with no arguments defaults to bump the build number.
$ ican bump
0.2.7-beta.3+build.100

# Now its release time.  Lets bump the minor
$ ican bump minor
0.3.0+build.101

# If we wanted to use the version to build a package for pypi
$ ican show public
0.3.0

# Oh no a bug, let's patch
$ ican bump patch
0.3.1+build.102
release pipeline output...

# Finally, our long awaited 1.0 release.
$ ican bump major
1.0.0+build.103
release pipeline output...

# Of course, our 1.0 release will be on pypi
$ ican show public
1.0.0
```

[^1]: The defaults are version '0.1.0' with auto-tag and auto-commit OFF.  For files to modify, all *.py files are searched for a __version__ string.
