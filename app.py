"""
Module to sync jira tasks to Hatchbuck.com CRM Deals
"""
import argparse
import logging
import os

# import pprint

from dotenv import load_dotenv

from jira import JIRA

LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def parse_arguments():
    """Parse arguments from command line"""
    parser = argparse.ArgumentParser(
        description="sync Jira tickets to Hatchbuck.com CRM"
    )
    parser.add_argument(
        "-n",
        "--noop",
        help="dont actually post/change anything,"
        " just log what would have been posted",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="set logging to debug",
        action="store_true",
        default=False,
    )
    args_parser = parser.parse_args()
    return args_parser


def main(args):
    """
    main function
    """
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)
    else:
        logging.basicConfig(format=LOGFORMAT)
    logging.debug("starting with arguments %s", args)
    jira = JIRA(
        server=os.environ.get("JIRA_URL", None),
        auth=(
            os.environ.get("JIRA_USERNAME", None),
            os.environ.get("JIRA_PASSWORD", None),
        ),
    )
    # The parenttickets list is a comma delimited string
    for parent in os.environ.get("JIRA_PARENTTICKETS", "").split(","):
        parent = parent.strip()
        project = parent.split("-")[0]
        enforce_parent_blocks(jira, project, parent, noop=args.noop)


def enforce_parent_blocks(jira, project, parent, noop=False):
    """
    enforce all tasks in project have a blocks link to (and only to) parent
    :param jira: jira connection
    :param project: project name
    :param parent: parent issue
    :param noop: no operation: dry run, don't actually change anything
    :return: None
    """
    logging.debug(
        "looking at project %s making sure all tasks are linked to %s", project, parent
    )
    tickets = jira.search_issues(
        "project={project} AND type = Task".format(project=project)
    )
    # pretty = pprint.PrettyPrinter()
    for ticket in tickets:
        # pretty.pprint(ticket.raw)
        parentfound = False
        for link in ticket.fields.issuelinks:
            if link.type.name == "Blocks" and hasattr(link, "outwardIssue"):
                if link.outwardIssue.key == parent:
                    parentfound = True
                    logging.debug("%s has block link to %s", ticket, parent)
                else:
                    if len(jira.worklogs(ticket)) > 0:
                        logging.warning(
                            "%s has rogue block link to %s, "
                            "but there are existing worklogs. ignoring.",
                            ticket,
                            link.outwardIssue.key,
                        )
                        continue
                    # found rogue block link that is not our parent
                    # delete this link and add the link to our parent below
                    logging.warning(
                        "%s has rogue block link to %s, removing",
                        ticket,
                        link.outwardIssue.key,
                    )
                    if not noop:
                        jira.delete_issue_link(link.id)
                    else:
                        logging.debug("noop")
            # print(link.raw)
        if not parentfound:
            if len(jira.worklogs(ticket)) > 0:
                logging.warning(
                    "%s has no block link to %s, "
                    "but there are existing worklogs. ignoring.",
                    ticket,
                    parent,
                )
                continue
            logging.warning("%s has no block link to %s, adding", ticket, parent)
            if not noop:
                jira.create_issue_link("Blocks", ticket, parent)
            else:
                logging.debug("noop")


if __name__ == "__main__":
    # load settings from .env for development
    load_dotenv()
    ARG = parse_arguments()
    main(ARG)
