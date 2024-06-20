import os
import logging
import json
import pytz
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Set up basic logging if the application is running in development
if os.environ.get("ENV") == "development":
    logging.basicConfig(level=logging.DEBUG)
elif os.environ.get("ENV") == "production":
    logging.basicConfig(level=logging.INFO)
    
# Function to store reminder timestamp in a file, ensuring one entry per channel
def store_reminder_ts(channel_id, message_ts):
    reminder_data = {
        "channel_id": channel_id,
        "message_ts": message_ts
    }

    try:
        with open('reminder_ts.json', 'r') as f:
            try:
                reminders = json.load(f)
            except json.JSONDecodeError:
                reminders = {}
    except FileNotFoundError:
        reminders = {}

    # Ensure only one entry per channel
    reminders[channel_id] = reminder_data

    with open('reminder_ts.json', 'w') as f:
        json.dump(reminders, f, indent=4)

# Function to retrieve reminder timestamp for a specific channel from a file
def get_reminder_ts(channel_id):
    try:
        with open('reminder_ts.json', 'r') as f:
            try:
                reminders = json.load(f)
                if channel_id in reminders:
                    reminder_data = reminders[channel_id]
                    return reminder_data["channel_id"], reminder_data["message_ts"]
            except json.JSONDecodeError:
                return None, None
    except FileNotFoundError:
        return None, None
    return None, None

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# The echo command simply echoes on command
@app.command("/notify-deploy")
def open_modal(ack, body, client):
    # Acknowledge command request
    ack()
    
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            "private_metadata": body["channel_id"],
            "callback_id": "deploy_modal",
            "title": {"type": "plain_text", "text": "Deployment Notification"},
            "submit": {"type": "plain_text", "text": "Send"},
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "plain_text",
                  "text": ":wave: Hey!\n\nPlease fill the form to notify the team about the latest deployment.",
                  "emoji": True
                }
              },
              {
                "type": "divider"
              },
              {
                "type": "input",
                "block_id": "project_name",
                "label": {
                  "type": "plain_text",
                  "text": "Project Name",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "action_id": "project_name-action"
                }
              },
              {
                "type": "input",
                "block_id": "deployment_type",
                "label": {
                  "type": "plain_text",
                  "text": "Deployment Type",
                  "emoji": True
                },
                "element": {
                  "type": "static_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select mode",
                    "emoji": True
                  },
                  "action_id": "deployment_type-action",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Production",
                        "emoji": True
                      },
                      "value": "Production"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Staging",
                        "emoji": True
                      },
                      "value": "Staging"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Development",
                        "emoji": True
                      },
                      "value": "Development"
                    }
                  ]
                }
              },
              {
                "type": "input",
                "block_id": "deployment_version",
                "label": {
                  "type": "plain_text",
                  "text": "Deployment Version",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "action_id": "deployment_version-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "e.g., v1.4.2 (Optional)",
                    "emoji": True
                  }
                },
                "optional": True
              },
              {
                "type": "input",
                "block_id": "task_links",
                "label": {
                  "type": "plain_text",
                  "text": "Key Changes & Tasks",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "task_links-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "List task links separated by new lines",
                    "emoji": True
                  }
                }
              },
              {
                "type": "input",
                "block_id": "additional_notes",
                "label": {
                  "type": "plain_text",
                  "text": "Additional Notes",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "additional_notes-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Any additional comments or notes? (Optional)",
                    "emoji": True
                  }
                },
                "optional": True
              }
            ]
        }
    )

@app.view("deploy_modal")
def handle_submission(ack, view, say):
    ack()
    
    channel_id = view["private_metadata"]
    project_name_value = view["state"]["values"]["project_name"]["project_name-action"]
    deployment_type_value = view["state"]["values"]["deployment_type"]["deployment_type-action"]["selected_option"]
    deployment_version_value = view["state"]["values"]["deployment_version"]["deployment_version-action"]
    task_links_value = view["state"]["values"]["task_links"]["task_links-action"]
    project_name = project_name_value.get('value')
    deployment_type = deployment_type_value.get('value')
    deployment_version = deployment_version_value.get('value')
    task_links = task_links_value.get('value')
    
    say(
      channel=channel_id,
      blocks=[
        {
        "type": "header",
        "text": {
          "type": "plain_text",
          "text": ":rocket: Deployment Notification :rocket:",
          "emoji": True
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"• Project: *{project_name}*\n• Mode: *{deployment_type}*, Version: *{deployment_version}*"
        }
      },
      {
        "type": "divider"
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": ":memo: *Key Changes & Tasks:*"
        }
      },
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": f"{task_links}"
        }
      },
      ],
      text=f"<@here>"
    )
    
   
# Opan the modal for the BA report
@app.command("/report-ba")
def report_ba_modal(ack, body, client):
    # Acknowledge command request
    ack()
    
    channel_id = body["channel_id"]
    
    channel_id, reminder_message_ts = get_reminder_ts(channel_id)
    if not reminder_message_ts:
        return client.chat_postMessage(channel=channel_id, text="No reminder message found.")
    
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            "private_metadata": f'{channel_id},{reminder_message_ts}',
            "callback_id": "report_ba_modal",
            "title": {"type": "plain_text", "text": "Deliverable Items Report"},
            "submit": {"type": "plain_text", "text": "Generate"},
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "plain_text",
                  "text": ":wave: Hi!\n\nPlease fill the form to generate the report.",
                  "emoji": True
                }
              },
              {
                "type": "divider"
              },
              {
                "type": "input",
                "block_id": "team_name",
                "label": {
                  "type": "plain_text",
                  "text": "Team Name",
                  "emoji": True
                },
                "element": {
                  "type": "static_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select name",
                    "emoji": True
                  },
                  "action_id": "team_name-action",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Core",
                        "emoji": True
                      },
                      "value": "Core"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Titan",
                        "emoji": True
                      },
                      "value": "Titan"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "AIS",
                        "emoji": True
                      },
                      "value": "AIS"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "App",
                        "emoji": True
                      },
                      "value": "App"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Badr",
                        "emoji": True
                      },
                      "value": "Badr"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "404",
                        "emoji": True
                      },
                      "value": "404"
                    }
                  ]
                }
              },
              {
                "type": "input",
                "block_id": "datepicker",
                "element": {
                  "type": "datepicker",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select a date",
                    "emoji": True
                  },
                  "action_id": "datepicker-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Date",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "deliverable_tickets",
                "label": {
                  "type": "plain_text",
                  "text": "Deliverable Tickets",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "deliverable_tickets-action"
                }
              },
              {
                "type": "input",
                "block_id": "definition_of_done",
                "label": {
                  "type": "plain_text",
                  "text": "Definition of Done",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "definition_of_done-action"
                }
              },
              {
                "type": "input",
                "block_id": "tested_tickets",
                "label": {
                  "type": "plain_text",
                  "text": "Tested Tickets",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "tested_tickets-action"
                }
              },
              {
                "type": "input",
                "block_id": "spent_time",
                "element": {
                  "type": "radio_buttons",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Yes",
                        "emoji": True
                      },
                      "value": "Yes"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "No",
                        "emoji": True
                      },
                      "value": "No"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "N/A",
                        "emoji": True
                      },
                      "value": "N/A"
                    }
                  ],
                  "action_id": "spent_time-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Update spent time sheet (all status)",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "project_status",
                "element": {
                  "type": "radio_buttons",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Yes",
                        "emoji": True
                      },
                      "value": "Yes"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "No",
                        "emoji": True
                      },
                      "value": "No"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "N/A",
                        "emoji": True
                      },
                      "value": "N/A"
                    }
                  ],
                  "action_id": "project_status-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Update project status sheet",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "sprint_plan",
                "element": {
                  "type": "radio_buttons",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Yes",
                        "emoji": True
                      },
                      "value": "Yes"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "No",
                        "emoji": True
                      },
                      "value": "No"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "N/A",
                        "emoji": True
                      },
                      "value": "N/A"
                    }
                  ],
                  "action_id": "sprint_plan-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Update sprint plan sheet",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "client_update",
                "element": {
                  "type": "radio_buttons",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Yes",
                        "emoji": True
                      },
                      "value": "Yes"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "No",
                        "emoji": True
                      },
                      "value": "No"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "N/A",
                        "emoji": True
                      },
                      "value": "N/A"
                    }
                  ],
                  "action_id": "client_update-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Did we update clients?",
                  "emoji": True
                },
                "optional": True
              },
              {
                "type": "input",
                "block_id": "why_failed",
                "label": {
                  "type": "plain_text",
                  "text": "Why failed to done?",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "why_failed-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Write in one sentence",
                    "emoji": True
                  }
                },
                "optional": True
              },
              {
                "type": "input",
                "block_id": "additional_notes",
                "label": {
                  "type": "plain_text",
                  "text": "Additional Notes",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "additional_notes-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Any additional comments or notes?",
                    "emoji": True
                  }
                },
                "optional": True
              }
            ]
        }
    )

@app.view("report_ba_modal")
def handle_submission_ba_report(ack, view, say):
    # Acknowledge the view_submission event
    ack()
    
    # Extract channel_id and reminder_message_ts from private_metadata
    channel_id, reminder_message_ts = view["private_metadata"].split(',')
    
    team_name_value = view["state"]["values"]["team_name"]["team_name-action"]["selected_option"]
    datepicker_value = view["state"]["values"]["datepicker"]["datepicker-action"]["selected_date"]
    deliverable_tickets_value = view["state"]["values"]["deliverable_tickets"]["deliverable_tickets-action"]
    definition_of_done_value = view["state"]["values"]["definition_of_done"]["definition_of_done-action"]
    tested_tickets_value = view["state"]["values"]["tested_tickets"]["tested_tickets-action"]
    spent_time_value = view["state"]["values"]["spent_time"]["spent_time-action"]["selected_option"]
    project_status_value = view["state"]["values"]["project_status"]["project_status-action"]["selected_option"]
    sprint_plan_value = view["state"]["values"]["sprint_plan"]["sprint_plan-action"]["selected_option"]
    client_update_value = view["state"]["values"]["client_update"]["client_update-action"]["selected_option"]
    why_failed_value = view["state"]["values"]["why_failed"]["why_failed-action"]
    additional_notes_value = view["state"]["values"]["additional_notes"]["additional_notes-action"]
    team_name = team_name_value.get('value')
    date = datepicker_value
    deliverable_tickets = deliverable_tickets_value.get('value')
    definition_of_done = definition_of_done_value.get('value')
    tested_tickets = tested_tickets_value.get('value')
    spent_time = spent_time_value.get('value')
    project_status = project_status_value.get('value')
    sprint_plan = sprint_plan_value.get('value')
    client_update = client_update_value.get('value')
    why_failed = why_failed_value.get('value')
    additional_notes = additional_notes_value.get('value')
    
    say(
      channel=channel_id,
      blocks=[
        {
          "type": "header",
          "text": {
            "type": "plain_text",
            "text": ":clipboard: Deliverable Items Report :clipboard:",
            "emoji": True
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Team: *{team_name}*\n• Date: *{date}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":bar_chart: *Report Summary:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Deliverable Tickets: *{deliverable_tickets}*\n• Definition of Done: *{definition_of_done}*\n• Tested Tickets: *{tested_tickets}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":chart_with_upwards_trend: *Project Status:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Update spent time sheet: *{spent_time}*\n• Update project status sheet: *{project_status}*\n• Update sprint plan sheet: *{sprint_plan}*\n• Update clients: *{client_update}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":warning: *Why failed to done:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"{why_failed}"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":memo: *Additional Notes:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"{additional_notes}"
          }
        },
      ],
      text=f"<@here>",
      thread_ts=reminder_message_ts
    )
    
# Opan the modal for the QA report
@app.command("/report-qa")
def report_qa_modal(ack, body, client):
    # Acknowledge command request
    ack()
    
    channel_id = body["channel_id"]
    
    channel_id, reminder_message_ts = get_reminder_ts(channel_id)
    if not reminder_message_ts:
        return client.chat_postMessage(channel=channel_id, text="No reminder message found.")
    
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            "private_metadata": f'{channel_id},{reminder_message_ts}',
            "callback_id": "report_qa_modal",
            "title": {"type": "plain_text", "text": "Deliverable Items Report"},
            "submit": {"type": "plain_text", "text": "Generate"},
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "plain_text",
                  "text": ":wave: Hi!\n\nPlease fill the form to generate the report.",
                  "emoji": True
                }
              },
              {
                "type": "divider"
              },
              {
                "type": "input",
                "block_id": "team_name",
                "label": {
                  "type": "plain_text",
                  "text": "Team Name",
                  "emoji": True
                },
                "element": {
                  "type": "static_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select name",
                    "emoji": True
                  },
                  "action_id": "team_name-action",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Core",
                        "emoji": True
                      },
                      "value": "Core"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Titan",
                        "emoji": True
                      },
                      "value": "Titan"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "AIS",
                        "emoji": True
                      },
                      "value": "AIS"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "App",
                        "emoji": True
                      },
                      "value": "App"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Badr",
                        "emoji": True
                      },
                      "value": "Badr"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "404",
                        "emoji": True
                      },
                      "value": "404"
                    }
                  ]
                }
              },
              {
                "type": "input",
                "block_id": "datepicker",
                "element": {
                  "type": "datepicker",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select a date",
                    "emoji": True
                  },
                  "action_id": "datepicker-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Date",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "deliverable_tickets",
                "label": {
                  "type": "plain_text",
                  "text": "Deliverable Tickets",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "deliverable_tickets-action"
                }
              },
              {
                "type": "input",
                "block_id": "definition_of_done",
                "label": {
                  "type": "plain_text",
                  "text": "Definition of Done",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "definition_of_done-action"
                }
              },
              {
                "type": "input",
                "block_id": "tested_tickets",
                "label": {
                  "type": "plain_text",
                  "text": "Tested Tickets",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "tested_tickets-action"
                }
              },
              {
                "type": "input",
                "block_id": "defects",
                "label": {
                  "type": "plain_text",
                  "text": "Defects",
                  "emoji": True
                },
                "element": {
                  "type": "number_input",
                  "is_decimal_allowed": False,
                  "action_id": "defects-action"
                }
              },
              {
                "type": "input",
                "block_id": "spent_time",
                "element": {
                  "type": "radio_buttons",
                  "options": [
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "Yes",
                        "emoji": True
                      },
                      "value": "Yes"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "No",
                        "emoji": True
                      },
                      "value": "No"
                    },
                    {
                      "text": {
                        "type": "plain_text",
                        "text": "N/A",
                        "emoji": True
                      },
                      "value": "N/A"
                    }
                  ],
                  "action_id": "spent_time-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Update Actual in Spent Time Sheet",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "problem",
                "label": {
                  "type": "plain_text",
                  "text": "Problems of the team",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "problem-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Write in one sentence",
                    "emoji": True
                  }
                },
                "optional": True
              },
              {
                "type": "input",
                "block_id": "additional_notes",
                "label": {
                  "type": "plain_text",
                  "text": "Additional Notes",
                  "emoji": True
                },
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "additional_notes-action",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Any additional comments or notes?",
                    "emoji": True
                  }
                },
                "optional": True
              }
            ]
        }
    )

@app.view("report_qa_modal")
def handle_submission_qa_report(ack, view, say):
    # Acknowledge the view_submission event
    ack()
    
    # Extract channel_id and reminder_message_ts from private_metadata
    channel_id, reminder_message_ts = view["private_metadata"].split(',')
    
    team_name_value = view["state"]["values"]["team_name"]["team_name-action"]["selected_option"]
    datepicker_value = view["state"]["values"]["datepicker"]["datepicker-action"]["selected_date"]
    deliverable_tickets_value = view["state"]["values"]["deliverable_tickets"]["deliverable_tickets-action"]
    definition_of_done_value = view["state"]["values"]["definition_of_done"]["definition_of_done-action"]
    tested_tickets_value = view["state"]["values"]["tested_tickets"]["tested_tickets-action"]
    defects_value = view["state"]["values"]["defects"]["defects-action"]
    spent_time_value = view["state"]["values"]["spent_time"]["spent_time-action"]["selected_option"]
    problem_value = view["state"]["values"]["problem"]["problem-action"]
    additional_notes_value = view["state"]["values"]["additional_notes"]["additional_notes-action"]
    team_name = team_name_value.get('value')
    date = datepicker_value
    deliverable_tickets = deliverable_tickets_value.get('value')
    definition_of_done = definition_of_done_value.get('value')
    tested_tickets = tested_tickets_value.get('value')
    spent_time = spent_time_value.get('value')
    defects = defects_value.get('value')
    problem = problem_value.get('value')
    additional_notes = additional_notes_value.get('value')
    
    say(
      channel=channel_id,
      blocks=[
        {
          "type": "header",
          "text": {
            "type": "plain_text",
            "text": ":clipboard: Deliverable Items Report :clipboard:",
            "emoji": True
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Team: *{team_name}*\n• Date: *{date}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":bar_chart: *Report Summary:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Deliverable Tickets: *{deliverable_tickets}*\n• Definition of Done: *{definition_of_done}*\n• Tested Tickets: *{tested_tickets}*\n• Defects: *{defects}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":chart_with_upwards_trend: *Project Status:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"• Update Actual in Spent Time Sheet: *{spent_time}*"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":warning: *Problems of the team:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"{problem}"
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": ":memo: *Additional Notes:*"
          }
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": f"{additional_notes}"
          }
        },
      ],
      text=f"<@here>",
      thread_ts=reminder_message_ts
    )

# Listens to incoming messages
@app.event("message")
def handle_message_events(body, logger):
  event = body.get("event", {})
  text = event.get("text", "")
  
  if "reminder" in text.lower():
      channel_id = event.get("channel")
      message_ts = event.get("ts")
      
      # store_reminder_ts(channel_id, message_ts)
      # logger.info(f"Stored reminder message ts: {message_ts}")
      
      # Convert timestamp to datetime in the Asia/Dhaka timezone
      reminder_time = datetime.fromtimestamp(float(message_ts), tz=pytz.UTC)
      reminder_time = reminder_time.astimezone(pytz.timezone('Asia/Dhaka'))

      if reminder_time.hour >= 20:  # 8 PM in 24-hour format
          store_reminder_ts(channel_id, message_ts)
          logger.info(f"Stored reminder message ts: {message_ts}")
      else:
          logger.info(f"Reminder received at {reminder_time.strftime('%Y-%m-%d %H:%M:%S %Z')}, not storing because it is not after 8 PM.")

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()