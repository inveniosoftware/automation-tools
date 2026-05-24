# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Contains the settings to repository modifications."""

from github import Github

# The organization name
organization = "inveniosoftware"

# Remote name
destination = "origin"

# Directory path to hold a copy of the repositories
local_repositories_path = '/path/to/inveniosoftware_cache'

# Github credentials / token
github = Github()
