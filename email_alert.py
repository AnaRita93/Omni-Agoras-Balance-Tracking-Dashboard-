import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from decouple import config
import pandas as pd 

changes_found_df = pd.read_csv('changes_found.csv')


# make sure to import the required modules and dataframe

def send_email_alert(subject, content):
    message = Mail(
        from_email='ar.oliveirasantos@egmail.com',
        to_emails='ar.oliveirasantos@gmail.com',
        subject=subject,
        plain_text_content=content
    )

    try:
        sg = sendgrid.SendGridAPIClient(config('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
   
    except Exception as e:
        print(str(e))

# Check if there are changes
if not changes_found_df.empty:
    # Create a string with the changes information
    changes_str = changes_found_df.to_string(index=False)

    # Add additional messages
    additional_msg1 = "Important balance changes were detected in the following addresses: "
    additional_msg2 = "For more details, please consult the dashboard here:http://144.91.121.7:8081/"

    # Combine all the strings
    message = additional_msg1+changes_str+additional_msg2

    # Send an email alert with the changes
    send_email_alert('Omni Agoras Balance Tracking', message)
 

