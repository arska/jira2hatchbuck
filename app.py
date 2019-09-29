import argparse
import logging
import os
import pprint

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
    args_parser = parser.parse_args()
    return args_parser


def main(args):
    """
    sync jira tickets to hatchbuck CRM
    """
    logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)
    logging.debug("starting with arguments %s",args)
    pretty = pprint.PrettyPrinter()
    jira = JIRA(
        server=os.environ.get("JIRA_URL", None),
        auth=(
            os.environ.get("JIRA_USERNAME", None),
            os.environ.get("JIRA_PASSWORD", None),
        ),
    )
    for parent in os.environ.get("JIRA_PARENTTICKETS","").split(","):
        parent = parent.strip()
        project = parent.split("-")[0]
        logging.debug("looking at project %s making sure all tasks are linked to %s",project,parent)
        tickets = jira.search_issues("project={project} AND type = Task".format(project=project))
        for ticket in tickets:
            #pretty.pprint(ticket.raw)
            parentfound = False
            for link in ticket.fields.issuelinks:
                if link.type.name == "Blocks" and hasattr(link, "outwardIssue"):
                    if link.outwardIssue.key == parent:
                        parentfound = True
                        logging.debug("%s has block to %s",ticket,parent)
                    else:
                        # found rogue blocks that is not our parent
                        # delete this link and add the link to our parent below
                        logging.info("%s has rogue block to %s, removing", ticket, link.outwardIssue.key)
                        if not args.noop:
                            jira.delete_issue_link(link.id)
                        else:
                            logging.debug("noop")
                #print(link.raw)
            if not parentfound:
                logging.info("%s has no block to %s, adding", ticket, parent)
                if not args.noop:
                    jira.create_issue_link("Blocks",ticket, parent)
                else:
                    logging.debug("noop")


if __name__ == "__main__":
    # load settings from .env for development
    load_dotenv()
    ARG = parse_arguments()
    main(ARG)
