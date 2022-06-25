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


# ican  :wave:

any deploy/build task you ask of it, the response is always: ican

```
can you bump my version to the next prerelease?
dev@macbook:~/proj$ ican 

can you use that version as a git tag and push a commit to the tag?
dev@macbook:~/proj$ ican 

can you deploy my new version by building a docker container and starting it?
dev@macbook:~/proj$ ican 
```

## Install  :floppy_disk:

Install the ican package via pypi

```shell
pip install ican
```

## Confige  :toolbox:

Config is done via the .ican file in your project's root diarectory.  Alternate file names can be configured via a master config in your home directory.

Sample .ican file

```ini
[version]
current = 0.1.6+build.40

[options]
auto-tag = True
auto-commit = True
auto-push = True
signature = True

[file1]
file = ./ican/__init__.py
style = semantic
regex = __version__\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)

```

## Use  :muscle: 

You can use ican via the CLI in a typical fashion, using the format below

```shell
ican [command] [arguments] [options] 
```

## Commands  :dog2:

| Command      | Arguments             | Description   |
| -------------| --------------------  | ------------- |
| bump       | **PART** `required`  |The **PART** would be: The segment of the semantic version to increase.  <br />Choices are [*major*, *minor*, *patch*, *prerelease*] |
| show       | **STYLE** `required` | The **STYLE** would be: The version style you want. <br />Choices are [*semantic*, *public*, *pep440*, *git*] |
| init       | none.                | This command would initialize your project in the current directory.                                |


## Options  :roll_eyes:  

The output and parsing of `ican` can be controlled with the following options.

| Name                   | Description                                                  |
| -------------          | -------------                                                |
| `--verbose`            | To aid in your debugging, verbose prints all messages.       |
| `--dry-run`            | Useful if used WITH --verbose, will not modify any files.    |
| `--version`            | This will displpay the current version of ican.              |
| `--canonical`          | Test if the pep440 version conforms to pypi's specs          |

## Examples  :eyes: 

```shell
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

# Finally, our long awaited 1.0 release.
$ ican bump major
1.0.0+build.103

# Of course, our 1.0 release will be on pypi
$ ican show public
1.0.0
```

[^1]: The defaults are version '0.1.0' with auto-tag and auto-commit OFF.  For files to modify, all *.py files are searched for a __version__ string.
