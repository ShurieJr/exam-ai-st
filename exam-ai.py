from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Exam Ai", layout="wide")

# assistant ID
assistant1 = "asst_knueiNbtyqAK8ZmJUuVbHvPs"
assistant2 = "asst_gci6pTe7sTgqzZPTOSSLqJaj"

# Define the pages
def generateExam():
    st.title('Exam Generator')
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
    total_questions = st.text_input("Total number of questions:")
    exam_parts = st.multiselect(
        "Select exam parts:",
        options=["1- True or False", "2- Fill in the Blank Spaces", "3- Multiple Choices", "4- Direct Questions"],
        default=["1- True or False", "2- Fill in the Blank Spaces"]
    )
    exam_difficulty = st.selectbox(
        "Select exam difficulty:",
        options=["Easy", "Medium", "Hard"],
        index=1  # Default selection is 'Medium'
    )
    exam_level = st.selectbox(
        "Select exam level:",
        options=["Primary", "High School", "University"],
        index=2  # Default selection is 'University'
    )
    submit = st.button('Generate Exam')

    if submit and uploaded_file is not None:
        # Upload the user provided file to OpenAI
        message_file = client.files.create(
            file=uploaded_file, purpose="assistants"
        )

        # Create a thread
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"please generate an exam based on the book. The exam should have at least three parts which are {', '.join(exam_parts)}, with a total of {total_questions} questions. The exam level is {exam_level} and the difficulty is {exam_difficulty}. Your output response should only be the exam text, without any extra instructions or answers.",
                    "attachments": [
                        {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ]
        )

        # Start run
        
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant1
        )

        # Outputting message
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        message_content = messages[0].content[0].text
        st.write(message_content.value)
    elif submit:
        st.error("Please upload a file to generate the exam.")

def correctExam():
    st.title('Exam Corrector')
    original_file = st.file_uploader("Original file", type="pdf")
    student_file = st.file_uploader("Student file", type="pdf")
    
    submit = st.button('Correct Exam')

    if submit is not None and student_file is not None and original_file is not None:
        # teacher files vector
        vector_store_f = client.beta.vector_stores.create(name="book file or teacher file or source of truth to use in order to correct student exam file that will be uploaded")
        file_streams = [original_file]
        # file_streams = [open(path, "rb") for path in file_paths]
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_f.id, files=file_streams
        )
        

        assistant = client.beta.assistants.update(
            assistant_id=assistant2,
            tool_resources={"file_search": {"vector_store_ids": [vector_store_f.id]}},
        )

        # student exam file
        
        message_file = client.files.create(
            file=student_file, purpose="assistants"
        )

        
        # Create a thread and attach the file to the message
        thread = client.beta.threads.create(
        messages=[
            {
            "role": "user",
            "content": "please correct this student exam file by using uploaded book as source of truth and tell me the score of the student and how many questions his got wrong ? ",
            "attachments": [
                { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
            ],

            }]
        )
    
        # Start run
        # Use the create and poll SDK helper to create a run and poll the status of
        # the run until it's in a terminal state.

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant2
        )

        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

        # Outputting message

        if messages:
            message_content = messages[0].content[0].text
            annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            st.write(message_content.value)
        else:
            st.error("No messages found in the thread.")

    elif submit:
        st.error("Please upload a file to correct the exam.")






# Sidebar for navigation
st.sidebar.title('Exam Ai')
page = st.sidebar.radio("Select a page:", options=["Exam Generator", "Exam Corrector"])

# Display the selected page
if page == "Exam Generator":
    generateExam()
elif page == "Exam Corrector":
    correctExam()

