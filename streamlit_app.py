import streamlit as st
import markdown
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

OPENAI_API_KEY = st.secrets["openai_api_key"]
SENDGRID_API_KEY = st.secrets["sendgrid_api_key"]


def send_email(receiver_email, workout_plan):
    html_content = markdown.markdown(workout_plan, extensions=['extra', 'sane_lists'])

    message = Mail(
        from_email='nxsfit0221@gmail.com',
        to_emails=receiver_email,
        subject='Your Custom Workout Plan from Nexus FitNow',
        plain_text_content=workout_plan,  # Send raw markdown as plain text
        html_content=html_content  # Rendered HTML content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent successfully! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Function to get workout plan from ChatGPT
def generate_workout_plan(goal, concerns, equipment, training_years, workout_duration, workout_type, focus_area):
    prompt = f"""
        Goal: {goal}
        Injuries, pains, concerns: {concerns}
        Available equipment: {equipment}
        Training years: {training_years}
        Required Workout Duration in Minutes: {workout_duration}
        Workout Type: {workout_type}
        Focus Area: {focus_area}
    """
    

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id="asst_EMeOkJZoPiRqwgQwqiu83zBR",
    )

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages.data[0].content[0].text.value)
    else:
        workout_plan = "Unable to generate workout plan. Please try again later."

    workout_plan = messages.data[0].content[0].text.value

    return workout_plan

# Streamlit app
def main():
    st.title("Nexus FitNow")

    # Step 1: Ask for user inputs
    st.header("First, tell us about yourself!")
    goal = st.selectbox("What is your primary fitness goal?", ["Build muscle", "Lose fat", "Gain strength", "Improve endurance", "Improve power"])
    concerns = st.text_input("Do you have any previous injuries, pains, weaknesses, tightness, or concerns?")
    equipment = st.text_input("What equipment do you have access to? (e.g., full gym, dumbbells, barbell, bands, treadmill)")
    training_years = st.number_input("How many years have you been training consistently?", min_value=0.0, step=.25)
    workout_duration = st.number_input("How long should the workout be? (in minutes)", min_value=10, step=5)
    workout_type = st.text_input("Do you have a type of workout that you'd like to do today?")
    focus_area = st.text_input("Is there a specific area that you'd like to focus on?")

    if st.button("Generate Program"):
        with st.spinner("Generating your custom program..."):
            workout_plan = generate_workout_plan(goal, concerns, equipment, training_years, workout_duration, workout_type, focus_area)
            st.session_state['workout_plan'] = workout_plan
            st.success("Program generated!")

    # Step 2: Display workout plan and create dynamic pages
    if "workout_plan" in st.session_state:
        st.header("Here is your custom workout! Let's Go!")
        try:
            workout_plan = st.session_state['workout_plan']
            st.markdown(workout_plan)

            st.header("Don't lose your custom workout. Get it sent to your email!")

            email = st.text_input("Enter your email address:")
            if st.button("Send to Email"):
                if email:
                    success = send_email(email, workout_plan)
                    if success:
                        st.success("Workout plan sent successfully!")
                    else:
                        st.error("Failed to send email. Please check your email address and try again.")
                else:
                    st.warning("Please enter a valid email address.")


        except Exception as e:
            st.error(f"Error parsing workout plan: {e}")

if __name__ == "__main__":
    main()
