Sync Jira Tickets to Hatchbuck CRM Deals
========================================

[![Build Status](https://travis-ci.com/arska/jira2hatchbuck.svg?branch=master)](https://travis-ci.com/arska/jira2hatchbuck)

## Configuration

Configuration through environment variables (or .env file):
* JIRA_SERVER=https://example.com/
* JIRA_USERNAME=myusername
* JIRA_PASSWORD=mypassword
* JIRA_PARENTTICKETS="PROJ-1, OTHER-3": get the project name from the prefix, ensure each task in the project has a "blocks" link to this and only this ticket if there are no worklogs
