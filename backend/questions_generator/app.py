import os
import json
from datetime import datetime

from rag_pipeline import (
    generate_interview,
    evaluate_descriptive_answer
)


# ============================================================
# INPUT HELPERS
# ============================================================

def get_integer(prompt, minimum=0):

    while True:

        try:
            value = int(input(prompt).strip())

            if value < minimum:
                print(f"Please enter a number >= {minimum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_job_description():

    print("\n" + "=" * 70)
    print("                    JOB DESCRIPTION")
    print("=" * 70)

    print("Enter the job description.")
    print("Type END on a new line when finished.\n")

    lines = []

    while True:

        line = input()

        if line.strip().upper() == "END":
            break

        lines.append(line)

    return "\n".join(lines).strip()


# ============================================================
# HR INTERVIEW CONFIGURATION
# ============================================================

def configure_interview():

    print("\n" + "=" * 70)
    print("                  INTERVIEW CONFIGURATION")
    print("=" * 70)

    print("""
1. MCQ
2. Descriptive
3. Mixed
""")

    while True:

        mode = input(
            "Select interview type (1/2/3): "
        ).strip()

        if mode in ["1", "2", "3"]:
            break

        print("Please select 1, 2, or 3.")

    total = get_integer(
        "\nTotal number of questions: ",
        minimum=1
    )

    print("\nDifficulty distribution")
    print("-" * 40)

    while True:

        easy = get_integer("Easy questions: ")
        medium = get_integer("Medium questions: ")
        hard = get_integer("Hard questions: ")

        if easy + medium + hard == total:
            break

        print(
            f"\nInvalid distribution."
            f"\nTotal questions = {total}"
            f"\nEasy + Medium + Hard = "
            f"{easy + medium + hard}\n"
        )

    return {
        "mode": mode,
        "total": total,
        "easy": easy,
        "medium": medium,
        "hard": hard
    }


# ============================================================
# DISPLAY QUESTION TO CANDIDATE
# IMPORTANT:
# NEVER DISPLAY ANSWER / SCORE / FEEDBACK HERE
# ============================================================

def display_question(question, number):

    print("\n")
    print("=" * 70)
    print(f"QUESTION {number}")
    print("=" * 70)

    print(
        f"Difficulty : {question['difficulty']}"
    )

    print(
        f"Type       : {question['type']}"
    )

    print()

    print(question["question"])

    # MCQ options only
    # Correct answer is NOT displayed.

    if question["type"] == "MCQ":

        print()

        for key, value in question["options"].items():

            print(
                f"{key}. {value}"
            )


# ============================================================
# MCQ EVALUATION
# INTERNAL ONLY
# ============================================================

def evaluate_mcq(
    question,
    candidate_answer
):

    candidate_answer = (
        candidate_answer
        .strip()
        .upper()
    )

    correct_answer = (
        question["correct_answer"]
        .strip()
        .upper()
    )

    if candidate_answer == correct_answer:

        return {
            "score": question["marks"],
            "max_score": question["marks"],
            "correct": True,
            "feedback": "Correct answer.",
            "correct_answer": correct_answer
        }

    return {
        "score": 0,
        "max_score": question["marks"],
        "correct": False,
        "feedback": question["explanation"],
        "correct_answer": correct_answer
    }


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # ========================================================
    # HR SETUP
    # ========================================================

    print("=" * 70)
    print("             AI INTERVIEW ASSESSMENT SYSTEM")
    print("=" * 70)

    print("\nHR CONFIGURATION")

    # --------------------------------------------------------
    # Resume
    # --------------------------------------------------------

    print(
        "\nEnter candidate resume PDF path."
    )

    resume_path = input(
        "Resume path: "
    ).strip()

    resume_path = resume_path.strip('"')

    if not os.path.isfile(resume_path):

        print(
            "\nResume file not found."
        )

        return

    if not resume_path.lower().endswith(".pdf"):

        print(
            "\nPlease provide a PDF file."
        )

        return

    # --------------------------------------------------------
    # Job Description
    # --------------------------------------------------------

    job_description = get_job_description()

    if not job_description:

        print(
            "\nJob description cannot be empty."
        )

        return

    # --------------------------------------------------------
    # Interview Configuration
    # --------------------------------------------------------

    config = configure_interview()

    # ========================================================
    # GENERATE QUESTIONS
    # ========================================================

    print("\n" + "=" * 70)
    print("                 GENERATING INTERVIEW")
    print("=" * 70)

    print("\nProcessing resume...")
    print("Creating embeddings...")
    print("Retrieving relevant resume information...")
    print("Generating interview questions...")

    try:

        interview = generate_interview(

            resume_path=resume_path,

            job_description=job_description,

            mode=config["mode"],

            total_questions=config["total"],

            easy_questions=config["easy"],

            medium_questions=config["medium"],

            hard_questions=config["hard"]
        )

    except Exception as e:

        print(
            "\nError while generating interview:"
        )

        print(e)

        return

    questions = interview["questions"]

    # ========================================================
    # CANDIDATE INTERVIEW
    # ========================================================

    print("\n" + "=" * 70)
    print("                 CANDIDATE INTERVIEW")
    print("=" * 70)

    print(
        "\nThe interview will now begin."
    )

    print(
        "Your answers will be recorded."
    )

    print(
        "Results will be provided after the interview."
    )

    results = []

    # ========================================================
    # ASK QUESTIONS
    # ========================================================

    for index, question in enumerate(
        questions,
        start=1
    ):

        # ----------------------------------------------------
        # Display ONLY question
        # ----------------------------------------------------

        display_question(
            question,
            index
        )

        print()

        # ====================================================
        # MCQ
        # ====================================================

        if question["type"] == "MCQ":

            while True:

                answer = input(
                    "\nYour answer (A/B/C/D): "
                ).strip().upper()

                if answer in [
                    "A",
                    "B",
                    "C",
                    "D"
                ]:
                    break

                print(
                    "Please enter A, B, C, or D."
                )

            # Evaluate internally
            evaluation = evaluate_mcq(
                question,
                answer
            )

            candidate_answer = answer

        # ====================================================
        # DESCRIPTIVE
        # ====================================================

        else:

            print(
                "\nYour answer:"
            )

            print(
                "(Type END_ANSWER when finished)"
            )

            answer_lines = []

            while True:

                line = input()

                if line.strip() == "END_ANSWER":
                    break

                answer_lines.append(line)

            candidate_answer = (
                "\n".join(answer_lines)
                .strip()
            )

            # ------------------------------------------------
            # AI evaluates internally
            # ------------------------------------------------

            try:

                evaluation = (
                    evaluate_descriptive_answer(

                        question=question,

                        candidate_answer=
                        candidate_answer
                    )
                )

            except Exception as e:

                # Don't show evaluation error to candidate
                # Store it internally.

                evaluation = {

                    "score": 0,

                    "max_score":
                        question["marks"],

                    "feedback":
                        "Evaluation failed.",

                    "strengths": [],

                    "improvements": []
                }

        # ====================================================
        # IMPORTANT
        # DO NOT DISPLAY EVALUATION TO CANDIDATE
        # ====================================================

        results.append({

            "question_number":
                index,

            "question":
                question,

            "candidate_answer":
                candidate_answer,

            "evaluation":
                evaluation
        })

        print("\nAnswer recorded.")

        if index < len(questions):

            print(
                "Moving to the next question..."
            )

    # ========================================================
    # INTERVIEW FINISHED
    # ========================================================

    print("\n")
    print("=" * 70)
    print("                 INTERVIEW COMPLETED")
    print("=" * 70)

    print(
        "\nThank you. Your interview has been completed."
    )

    print(
        "The assessment will be reviewed by HR."
    )

    # ========================================================
    # CALCULATE FINAL SCORE
    # ========================================================

    total_score = 0
    maximum_score = 0

    for result in results:

        evaluation = result["evaluation"]

        total_score += float(
            evaluation["score"]
        )

        maximum_score += float(
            evaluation["max_score"]
        )

    percentage = (

        (total_score / maximum_score) * 100

        if maximum_score > 0

        else 0
    )

    # ========================================================
    # HR REPORT
    # ========================================================

    report = {

        "generated_at":
            datetime.now().isoformat(),

        "resume":
            resume_path,

        "job_description":
            job_description,

        "configuration":
            config,

        "questions":
            results,

        "final_score":
            total_score,

        "maximum_score":
            maximum_score,

        "percentage":
            round(percentage, 2)
    }

    # ========================================================
    # SAVE REPORT
    # ========================================================

    os.makedirs(
        "reports",
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    json_path = (
        f"reports/"
        f"hr_interview_report_"
        f"{timestamp}.json"
    )

    txt_path = (
        f"reports/"
        f"hr_interview_report_"
        f"{timestamp}.txt"
    )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # HR TEXT REPORT
    # --------------------------------------------------------

    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "AI INTERVIEW ASSESSMENT - HR REPORT\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        file.write(
            f"Generated: "
            f"{report['generated_at']}\n\n"
        )

        file.write(
            f"Total Score: "
            f"{total_score}/{maximum_score}\n"
        )

        file.write(
            f"Percentage: "
            f"{percentage:.2f}%\n\n"
        )

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            "QUESTION-WISE ASSESSMENT\n"
        )

        file.write(
            "=" * 70 + "\n\n"
        )

        for result in results:

            question = result["question"]

            evaluation = result["evaluation"]

            file.write(
                f"QUESTION "
                f"{result['question_number']}\n"
            )

            file.write(
                "-" * 50 + "\n"
            )

            file.write(
                f"Type: "
                f"{question['type']}\n"
            )

            file.write(
                f"Difficulty: "
                f"{question['difficulty']}\n"
            )

            file.write(
                f"Marks: "
                f"{question['marks']}\n\n"
            )

            file.write(
                f"Question:\n"
                f"{question['question']}\n\n"
            )

            # ------------------------------------------------
            # MCQ HR information
            # ------------------------------------------------

            if question["type"] == "MCQ":

                file.write(
                    f"Options:\n"
                )

                for key, value in (
                    question["options"].items()
                ):

                    file.write(
                        f"{key}. {value}\n"
                    )

                file.write(
                    f"\nCandidate Answer: "
                    f"{result['candidate_answer']}\n"
                )

                file.write(
                    f"Correct Answer: "
                    f"{question['correct_answer']}\n"
                )

                file.write(
                    f"Explanation: "
                    f"{question['explanation']}\n"
                )

            # ------------------------------------------------
            # Descriptive HR information
            # ------------------------------------------------

            else:

                file.write(
                    f"Expected Answer:\n"
                    f"{question['expected_answer']}\n\n"
                )

                file.write(
                    f"Rubric:\n"
                )

                for item in question["rubric"]:

                    file.write(
                        f"- {item}\n"
                    )

                file.write(
                    "\n"
                )

                file.write(
                    f"Candidate Answer:\n"
                    f"{result['candidate_answer']}\n"
                )

            # ------------------------------------------------
            # Evaluation
            # ------------------------------------------------

            file.write(
                f"\nScore: "
                f"{evaluation['score']}/"
                f"{evaluation['max_score']}\n"
            )

            file.write(
                f"\nAI Feedback:\n"
                f"{evaluation['feedback']}\n"
            )

            if evaluation.get("strengths"):

                file.write(
                    "\nStrengths:\n"
                )

                for item in evaluation[
                    "strengths"
                ]:

                    file.write(
                        f"- {item}\n"
                    )

            if evaluation.get(
                "improvements"
            ):

                file.write(
                    "\nAreas for Improvement:\n"
                )

                for item in evaluation[
                    "improvements"
                ]:

                    file.write(
                        f"- {item}\n"
                    )

            file.write(
                "\n" + "=" * 70 + "\n\n"
            )

        # ----------------------------------------------------
        # Final HR summary
        # ----------------------------------------------------

        file.write(
            "\nFINAL HR SUMMARY\n"
        )

        file.write(
            "=" * 70 + "\n"
        )

        file.write(
            f"Total Score: "
            f"{total_score}/{maximum_score}\n"
        )

        file.write(
            f"Percentage: "
            f"{percentage:.2f}%\n"
        )

    # ========================================================
    # HR REPORT LOCATION
    # ========================================================

    print("\n")
    print("=" * 70)
    print("                    HR REPORT READY")
    print("=" * 70)

    print(
        f"\nJSON report:"
        f"\n{json_path}"
    )

    print(
        f"\nHR text report:"
        f"\n{txt_path}"
    )

    print(
        "\nOnly the HR report contains:"
    )

    print(
        "- Scores"
    )

    print(
        "- Correct answers"
    )

    print(
        "- Expected answers"
    )

    print(
        "- AI feedback"
    )

    print(
        "- Strengths"
    )

    print(
        "- Areas for improvement"
    )


if __name__ == "__main__":
    main()