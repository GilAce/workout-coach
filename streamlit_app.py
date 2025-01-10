import streamlit as st
import markdown
import urllib.parse
import re
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

OPENAI_API_KEY = st.secrets["openai_api_key"]
SENDGRID_API_KEY = st.secrets["sendgrid_api_key"]


def insert_google_links(workout_plan):
    # Find markers <<<Exercise>>> and replace them with markdown links
    def replace_with_link(match):
        exercise_name = match.group(1)
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(exercise_name)}"
        return f"[{exercise_name}]({search_url})"
    
    # Use regex to find and replace markers <<<Exercise>>>
    updated_plan = re.sub(r'<<<(.*?)>>>', replace_with_link, workout_plan)
    return updated_plan


def send_email(receiver_email, workout_plan):
 # Append a feedback request to the workout plan

    intro = """
Hi there!

Here's you're workout!

Best regards,

Your amigos at Nexus Fitness :)

P.S If you'd like a new program: [Go to Nexus FitNow!](https://workout-coach-oa7cwi8iywk.streamlit.app/)

---

    """

    feedback_request = """

---
        
### We'd love your feedback!

Please let us know what you think about your custom workout plan. Simply reply to this email with your thoughts or suggestions!

Your feedback helps us improve and provide the best possible experience. Thank you!

To ensure you’re off to a strong start, here are a few questions to help us refine your workout experience:

- Does this plan match your fitness goals and current lifestyle? If not, what changes would make it better?

- How did your first session go? Was it too easy, too hard, or just right?

- Did you need to modify the workout? If so, what did you change, and why?

- What’s one thing you’d love to see in your next plan?
    """

    # Add the feedback request to both the plain text and HTML versions
    workout_plan_with_intro_and_feedback = intro + \
        "\n" + workout_plan + "\n" + feedback_request
    html_content_with_intro_and_feedback = markdown.markdown(
        workout_plan_with_intro_and_feedback, extensions=['extra', 'sane_lists'])

    # Create the email message
    message = Mail(
        from_email='nxsfit0221@gmail.com',
        to_emails=receiver_email,
        subject='Your Custom Workout Plan from Nexus FitNow',
        plain_text_content=workout_plan_with_intro_and_feedback,  # Plain text with feedback
        html_content=html_content_with_intro_and_feedback  # Rendered HTML with feedback
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
        - Goal: {goal}
        - Injuries/Pains: {concerns}
        - Equipment: {equipment}
        - Training Years: {training_years}
        - Duration: {workout_duration} minutes
        - Workout Type: {workout_type}
        - Focus Area: {focus_area}
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
        assistant_id="asst_0BwF5ADrrHYMXacxytCSgrkS",
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
    st.title("Nexus FitNow (Beta)")

    # Step 1: Ask for user inputs
    st.header("First, tell us about yourself!")

    goal = st.selectbox(
        label="What is your main fitness goal for this workout?",
        placeholder="Choose one from the list.",
        options=["Build muscle", "Lose fat", "Gain strength", "Improve endurance", "Improve power", "Injury Prevention/Rehab"],
        index=None)
    training_years = st.number_input(
        label="How long have you been consistently working out? (in years)", 
        min_value=0.0, 
        step=.25)
    workout_duration = st.number_input(
        label="How much time do you have for your workout today? (in minutes)", 
        min_value=10, 
        step=5, 
        value=30)
    
    concerns = st.text_area(
        label="Do you have any injuries, pain points, or mobility issues? (optional)",
        placeholder="Examples: Lower back pain, knee pain, tight hamstrings, recovering from a shoulder injury, etc.")
    equipment = st.text_area(
        label="What equipment do you have access to for this workout? (optional)",
        placeholder="Examples: Full Gym, Dumbbells, Resistance Bands, Barbell, Treadmill, or None. Note: Equipment will be used only if it aligns with your goals and preferences.")
    workout_type = st.text_area(
       label="What kind of workout are you in the mood for today? (optional)",
       placeholder="Examples: Full body, cardio, legs, light intensity, upper body focus, etc.")
    focus_area = st.text_area(
        label="Which muscle group or movement would you like to emphasize? (optional)",
        placeholder="Examples: Core, arms, glutes, balance exercises, etc.")

    if st.button("Generate Program"):
        with st.spinner("Generating your custom program..."):
            workout_plan = generate_workout_plan(
                goal, concerns, equipment, training_years, workout_duration, workout_type, focus_area)
            workout_plan = insert_google_links(workout_plan)
            print(workout_plan)
            st.session_state['workout_plan'] = workout_plan
            st.success("Program generated!")

    # Step 2: Display workout plan and create dynamic pages
    if "workout_plan" in st.session_state:
        st.header("Here is your custom workout! Let's Go!")
        try:
            workout_plan = st.session_state['workout_plan']
            st.markdown(workout_plan, unsafe_allow_html=True)

            st.header(
                "Don't lose your custom workout. Get it sent to your email!")

            email = st.text_input("Enter your email address:")
            if st.button("Send to Email"):
                if email:
                    success = send_email(email, workout_plan)
                    if success:
                        st.success("Workout plan sent successfully!")
                    else:
                        st.error(
                            "Failed to send email. Please check your email address and try again.")
                else:
                    st.warning("Please enter a valid email address.")

        except Exception as e:
            st.error(f"Error parsing workout plan: {e}")


if __name__ == "__main__":
    main()
