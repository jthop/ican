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

because anything you ask of it, the response is **always** `ican`

## :man_office_worker: Motivation

There may be many similar programs.  But ican is the only version bumper/task runner/code releaser that is designed for small or even the 1 man team.

The one man team can have different procedures than larger teams.  When a "new version" is finished, often times you may forget to even increment it.  And when you run the new version, you're bound to find bugs.  Sometimes I may be deploying something to a docker container, and re-build the container 20 or 30 times just to do some decent debugging.  Do I increment the version each time?  No.  Of course not.  That is my motivation for the build number.

With ican the build number is always incremented and never reset.  This way if you run your pipeline to build a container 20 times or so, at least your version has a new build # each time.  Once you define a few pipelines too, you may even do more version incrementing than you used to.

Now, your one man team software can have a changelog, git activity, and version numbers that suggest to others you are a fully staffed company.

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

[aliases]
deploy = bump build

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
- The new.release pipeline will run on bump [patch, minor, or major].
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
| file: [LABEL]     | regex           | User-supplied python formattted regex string defining how to replace the file's version. [^1] |
| pipeline: [LABEL] | [STEP]            | A pipeline step is a cli command such as `git commit -a`.  **STEP values MUST to be unique.**  [^2]  |


### :mag: [^1]: User-supplied regex

When searching for a variable, ican will search for the variable's name, followed by an `=` symbol, followed by a value in either single or double quotes.  There can be spaces or no spaces on either side of the `=` symbol.  This covers most use cases.

If your use case is more complicated, you can omit the `variable` line in your config file and instead include a `regex` value instead.  This should be a pyton formatted regex string with a named group to identify the `version` ican will replace.


```ini
[file1]
file = ./src/__init__.py
style = semantic
regex = __version__\s*=\s*(?P<quote>[\'\"])(?P<version>.+)(?P=quote)
```

### :computer: [^2]: Pipelines

#### Labels

Pipeline labels have 2 purposes:
    * The label is used when using `ican run LABEL`.  This way we know which pipeline to run.
    * Certain labeled pipelines are automatically run.  These are labels that match a version's 'stage'
        - new.release - bump [major, minor, patch]
        - new.prerelease - bump [prerelease]
        - rebuild.release - bump[build] when prerelase is not set
        - rebuild.prerelease - bump[build] when prerelease is set

#### Pipeline Context

The context can be referenced 2 places in your pipelines
    * When writing pipelines you can use Jinja-style templating to insert contextual variables into the step. For example `git push origin master {{tag}}`
    * Ican will inject all context variables into the shell's environment as well when running pipeline steps.  This makes them available to any script you are running in the pipeline.

#### Pipeline Context Variables

| Variable      | Description                                      |
| --------------|--------------------------------------------------|
| semantic      | the current version in semantic format           |
| public        | the current version in public format             |
| pep440        | the current version canonical with pep440        |
| git           | the current version using git metadata           |
| previous      | the previous semantic version                    |
| tag           | the git tag, `v{public_version}`                 |
| age           | REBUILD if bump build, NEW all other bumps       |
| env           | DEVELOPMENT or PRODUCTION based on the version   |
| stage         | AGE . (RELEASE or PRERELEASE) ex NEW.RELEASE     |
| root          | the root directory of your project               |

## :muscle: Use

You can use ican via the CLI in a typical fashion, using the format below

```shell
ican [command] [arguments] [options]
```

## :dog2: Commands

| Command    | Arguments               | Options        | Description   |
| -----------| ------------------------| -------------  | ------------- |
| bump       | **PART** `required`     |                | Increments the **PART** of the semantic version.  <br /> [*major*, *minor*, *patch*, *prerelease*] |
| bump       |                         | --pre PRE      | If using prerelease, **PRE** allows you to set [*alpha*, **beta**, *rc, *dev] |
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

[^1]: The defaults are version '0.1.0' with auto-tag and auto-commit OFF.  For files to modify, all *.py files are searched for a __version__ string.

[^2]:
