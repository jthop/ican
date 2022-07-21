[![build, publish, and release](https://github.com/jthop/ican/actions/workflows/build_pub_release.yml/badge.svg)](https://github.com/jthop/ican/actions/workflows/build_pub_release.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://badge.fury.io/py/ican.svg)](https://badge.fury.io/py/ican)
[![CodeFactor](https://www.codefactor.io/repository/github/jthop/ican/badge)](https://www.codefactor.io/repository/github/jthop/ican)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![GitHub last commit](https://img.shields.io/github/last-commit/jthop/ican)](https://github.com/jthop/ican)
[![GitHub repo size](https://img.shields.io/github/repo-size/jthop/ican?style=flat)](https://github.com/jthop/ican)
[![GitHub language count](https://img.shields.io/github/languages/count/jthop/ican?style=flat)](https://github.com/jthop/ican)
[![GitHub top language](https://img.shields.io/github/languages/top/jthop/ican?style=flat)](https://python.org)
[![Whos your daddy](https://img.shields.io/badge/whos%20your%20daddy-2.0.7rc3-brightgreen.svg)](https://14.do/)
[![works badge](https://cdn.jsdelivr.net/gh/nikku/works-on-my-machine@v0.2.0/badge.svg)](https://github.com/nikku/works-on-my-machine)


# :wave: ican

Because anything you ask of it, the response is **always** `ican`.

## :man_office_worker: Motivation

There are plenty of version bumpers and build tools.  But ican is the only one that is designed for the smallest teams, even the 1 man team.

The one man team has different procedures than most.  Often times the one man team forgets to bump version numbers.  Few even bother to keep a code repository besides their own "Dropbox."

ican brings big team development practices to small teams.  ican's build number is one feature.  As long as you use ican to automate your docker image builds, deployments, etc. each time your build number is incremented.  That way you always have a different semantic version number, even if you don't purposely bump one of the primary 3 parts.

You can even easily use ican to start tagging docker images, as well as git commits.  Soon your small team will be officially "tagging" and "releasing" software like you have a Fortune 500 CI/CD manager.

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
log_file = ican.log

[file: version]
file = ./src/__init__.py
style = semantic
variable = __version__

[pipeline: new.release]
step1 = ./clean_my_project.sh
step2 = git commit -a
step3 = git tag -a {{tag}} --sign
step4 = git push origin master {{tag}}

```

### Explanation

- This config defines the current version as `0.1.6` with build # 40.
- All operations will be logged to the `ican.log` file.
- ican will update a variable named `__version__` in `./src/__init__.py` any time the bump command is run.
- ican will use the `semantic` style of the version when updating this file.
- All pipeline steps are typically shell-based commands.

### :exclamation: Important
Take note, all sections must be unique.  So if you define more than one <file: [LABEL]> section, make sure each one has a unique label.

The same is true for `pipeline` sections.  Each pipeline section must have a unique label.

### :thumbsdown: :exploding_head:
```ini
[file: py_code]
file = ./src/__init__.py
...
[file: py_code]
file = ./src/__main__.py
```

### :thumbsup: :sunglasses:
```ini
[file: src_init]
file = ./src/__init__.py
...
[file: main]
file = ./src/__main__.py
```

## :triangular_ruler: Config

| Section           | Key             | Value                                           |
| ----------------- | ----------------|-------------------------------------------------|
| version           | current         | This is the value that ican stores the current version number in. |
| version           | previous        | This is the previous version ican uses in case of rollback.       |
| options           | log_file        | All operations are logged to disk in this file.  To turn logging off, do not define the log_file. |
| aliases           | [ALIAS]         | Built-in command + args that [ALIAS] will trigger.  Example `bump patch` |
| file: [LABEL]     | file            | The filename of a file ican will update with new versions.  You can use a standard unix glob (*.py) if desired. |
| file: [LABEL]     | style           | The version format to use.  Choices are [semantic, public, pep440, git] |
| file: [LABEL]     | variable        | The variable name pointing to the version string that ican will update when versions are bumped. |
| file: [LABEL]     | regex           | User-supplied python formattted regex string defining how to replace the file's version. |
| pipeline: [LABEL] | [STEP]            | A pipeline step is a cli command such as `git commit -a`.  **STEP values MUST to be unique.**  |


### :mag: User-supplied regex

When searching for a variable, ican will search for the variable's name, followed by an `=` symbol, followed by a value in either single or double quotes.  There can be spaces or no spaces on either side of the `=` symbol.  This covers most use cases.

If your use case is more complicated, you can omit the `variable` line in your config file and instead include a `regex` value instead.  This should be a pyton formatted regex string with a named group to identify the `version` ican will replace.


```ini
[file1]
file = ./src/__init__.py
style = semantic
regex = __version__\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)
```

### :computer: Pipelines

#### Labels 
Pipeline labels can be used in 2 ways:

* At the CLI using `ican run LABEL`.  This way we know which pipeline to run.
* You can also run use the lazy technique and simply run `ican LABEL`.  ican should find your pipeline and run it

#### Pipeline Context
The pipeline context is available in 2 locations

* In the pipeline itself, you can use Jinja-style templating. Example: `git push origin master {{tag}}`
* Before a pipeline runs, ican will inject your shell's environment with all pipeline context variables prefixed with ICAN_.

For example you can access `semantic` in your ENV as `ICAN_SEMANTIC`

#### Pipeline Context Variables

| variable      | Description                                      |
| --------------|--------------------------------------------------|
| semantic      | the current version in semantic format           |
| public        | the current version in public format             |
| pep440        | the current version canonical with pep440        |
| git           | the current version using git metadata           |
| major         | the major portion of the semantic version        |
| minor         | the minor portion of the semantic version        |
| patch         | the patch portion of the semantic version        |
| prerelease    | the major portion of the semantic version        |
| build         | the build number                                 |
| tag           | the git tag, `v{public_version}`                 |
| age           | REBUILD if bump build, NEW all other bumps       |
| env           | DEVELOPMENT or PRODUCTION based on the version   |
| root          | the root directory of your project               |
| previous      | the previous semantic version                    |

## :muscle: Use

You can use ican via the CLI in a typical fashion, using the format below

```shell
ican [command] [arguments] [options]
```

## :dog2: Commands

| Command    | Arguments               | Options        | Description   |
| -----------| ------------------------| -------------  | ------------- |
| bump       | **PART** `required`     |                | Increments the **PART** of the semantic version.  <br /> [*major*, *minor*, *patch*, *prerelease*] |
| bump       |                         | --pre `TOKEN`  | If bumping prerelease, set the **TOKEN** to [*alpha*, *beta*, *rc*, *dev*] |
| pre        | **TOKEN** `required`    |                | Set the prerelease **TOKEN** without bumping.
| show       | **STYLE** `required`    |                | Shows the current version with the format **STYLE**. <br /> [*semantic*, *public*, *pep440*, *git*] |
| run        | **PIPELINE** `required` |                | Run the specified **PIPELINE**  |
| rollback   | none                    |                | Rollback to the previously persisted version.  |
| init       | none                    |                | Initialize your project with default config in the current directory.   |


## :roll_eyes: Options

The output and parsing of `ican` can be controlled with the following options.

| Name                   | Description                                                  |
| -------------          | -------------                                                |
| `--verbose`            | To aid in your debugging, verbose prints all messages.       |
| `--dry-run`            | Useful if used WITH --verbose, will not modify any files.    |
| `--version`            | This will displpay the current version of ican.

## :eyes: Examples

```bash
$ ican init

...

$ ican show current
0.2.7-beta.3+build.99

# Bump with no arguments defaults to bump the build number.
$ ican bump
0.2.7-beta.3+build.100

# Now its release time.  Lets bump the minor
$ ican bump minor
0.3.0+build.101

# Oh no, major problem, rollback
$ ican rollback
0.3.0+build.100

# Use an aliaw
$ ican deploy
+BEGIN pipeline.NEW.RELEASE
git commit successful
+END pipeline.NEW.RELEASE
1.0.0+build.101

# now run our docker pipeline
$ ican run docker
+BEGIN pipeline.DOCKER
docker container build...
+END pipeline.DOCKER
1.0.0+build.101
```
