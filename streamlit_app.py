import streamlit as st
from openai import OpenAI

# Set OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai_api_key"]


# Function to get workout plan from ChatGPT
def generate_workout_plan(goal, concerns, equipment, training_years, workout_duration):
    prompt = f"""
        Goal: {goal}
        Injuries, pains, concerns: {concerns}
        Available equipment: {equipment}
        Training years: {training_years}
        Desired Workout Duration in Minutes: {workout_duration}
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
        assistant_id="asst_yJR9QbP5Jd2iJefc23unnViw",
    )

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages.data[0].content[0].text.value)
    else:
        print(run.status)

    workout_plan = messages.data[0].content[0].text.value

    return workout_plan

# Streamlit app
def main():
    st.title("Custom Fitness Program Generator")

    # Step 1: Ask for user inputs
    st.header("Step 1: Tell us about yourself")
    goal = st.selectbox("What is your primary fitness goal?", ["Build muscle", "Lose fat", "Gain strength", "Improve endurance"])
    concerns = st.text_area("Do you have any previous injuries, pains, or concerns?")
    equipment = st.text_input("What equipment do you have access to? (e.g., dumbbells, barbell, treadmill)")
    training_years = st.number_input("How many years have you been training consistently?", min_value=0.0, step=.25)
    workout_duration = st.number_input("How long should the workout be? (in minutes)", min_value=10, step=5)


    if st.button("Generate Program"):
        with st.spinner("Generating your custom program..."):
            workout_plan_json = generate_workout_plan(goal, concerns, equipment, training_years, workout_duration)
            st.session_state['workout_plan'] = workout_plan_json
            st.success("Program generated!")

    # Step 2: Display workout plan and create dynamic pages
    if "workout_plan" in st.session_state:
        st.header("Step 2: Your Custom Workout Plan")
        try:
            # Parse the JSON into a Python dictionary
            workout_plan = eval(st.session_state['workout_plan'])  # Convert JSON string to dictionary
            st.json(workout_plan)

            # Generate dynamic workout pages
            st.header("Step 3: Track Your Workout")
            for exercise in workout_plan["program"]:
                st.subheader(f"Exercise: {exercise['exercise']}")
                st.write(f"**Sets:** {exercise['sets']}")
                if('recommendedRestPeriodInSeconds' in exercise):
                    st.write(f"**Rest Period:** {exercise['recommendedRestPeriodInSeconds']} seconds")
                st.write(f"**Notes:** {exercise['notes']}")
                if "recommendedReps" in exercise:
                    st.write(f"**Recommended Reps per Set:** {exercise['recommendedReps']}")
                if "timeInSeconds" in exercise:
                    st.write(f"**Recommended Time per Set (seconds):** {exercise['timeInSeconds']}")

                # Inputs for tracking progress
                for set_num in range(1, exercise['sets'] + 1):
                    st.write(f"Set {set_num}:")
                    weight = st.number_input(
                        f"Weight used for {exercise['exercise']} (Set {set_num}) in lbs/kg:",
                        min_value=0.0, step=0.25, key=f"{exercise['exercise']}_set_{set_num}_weight"
                    )
                    repetitions = st.number_input(
                        f"Reps completed for {exercise['exercise']} (Set {set_num}):",
                        min_value=0, step=1, key=f"{exercise['exercise']}_set_{set_num}_reps"
                    )
                    notes = st.text_area(
                        f"Notes/comments for {exercise['exercise']} (Set {set_num}):",
                        key=f"{exercise['exercise']}_set_{set_num}_notes"
                    )
                st.write("---")

        except Exception as e:
            st.error(f"Error parsing workout plan: {e}")

if __name__ == "__main__":
    main()
