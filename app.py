import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# The echo command simply echoes on command
@app.command("/notify-deploy")
def opal_modal(ack, body, client):
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
    
# Listens to incoming messages
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()