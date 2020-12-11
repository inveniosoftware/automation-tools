# ga-migration

This folder contains the scripts used to migrate a repository from Travis CI to GitHub actions.

The migration pipeline is *idempotent*, meaning you should be able to run it how many times you want, getting the same results.

The `utils.py` file contains the tasks implementations, while `main.py` imports and applies them according to our needs. `gitflow.py` handles the higher level git and github procedures.

## Install

```bash
# Activate a virtualenv and install pip requirements
virtualenv ~/.virtualenvs/ga-migration
source ~/.virtualenvs/ga-migration/bin/activate
pip install -r requirements.txt
```

## Migration

To apply migration patches on a cloned repository, run `python main.py --targetpath=invenio-records`.

E.g.:

```bash
# clone a repository
git clone https://github.com/inveniosoftware/invenio-records /some/dir/invenio-records
# run the migration scripts on it
python main.py --targetpath=/some/dir/invenio-records
# cd to the cloned repo
cd /some/dir/invenio-records
# check what appened
git status
git diff 
```

To apply the migration patches on a list of cloned repositories, specify them as `REPO_PATHS_TO_MIGRATE` in `config.py`:

```py
# git clone https://github.com/inveniosoftware/invenio-records
# git clone https://github.com/inveniosoftware/invenio-queues
REPO_PATHS_TO_MIGRATE = ["invenio-records", "invenio-queues"]
```

and then run the script without any argument:

```bash
python main.py
```

To modify the tasks and edit the pipeline, check `migrate_repo` in `main.py`.

## Full git/GitHub pipeline

`gitflow.py` implements the whole git pipeline:

- **Clone** the repository
- Look for the most recent commit where `.travis.yml` was still present
- **Checkout** a new branch from that commit
- Apply the [migration](#migration) patches
- **Add** the modifications and commit them
- **Push** the new `ga-migrate` branch to the github origin
- Look for an Issue mentioning the migration
	- If it's not there, open a new one
- **Open a PR** to merge `ga-migrate` to `master`, linking the migration Issue

To run the whole pipeline given a repository name inside the `inveniosoftware` GitHub org:

```bash
GH_ACCESS_TOKEN=$TOKEN python gitflow.py --reponame=invenio-records
```

Get a GitHub access token at https://github.com/settings/tokens/new, making sure to add read/write permissions. Actions will be taken on behalf of the user that generated the token and git commits will use the default git configuration, so set it accordingly.