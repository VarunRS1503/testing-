import streamlit as st
from crewai import Process, Agent, Task, Crew
from langchain_groq import ChatGroq 
from agents import compliance_agents, compliance_agents_tasks
from utils import extract_compliance_issues, format_compliance_issues, split_compliance_issues

def main():
    st.title("Compliance Monitoring Interface")
    st.write("Perform compliance issue monitoring on loan recovery conversations in Hindi.")

    # Text input
    text = st.text_area("Enter Text", height=200)
    if st.button("Analyze Compliance"):
        if text:
            # Define structures
            compliance_structure = '''{
                "compliance_issues": [
                    {
                        "issue_occurred": "code and Name of the compliance issue identified",
                        "conversation_part": "<text_excerpt_from_conversation where the non-compliance has occurred>"
                    }
                ]
            }'''

            # Initialize agents and tasks
            agent = compliance_agents()
            compliance_monitor_agent = agent.compliance_monitor()
            tasks = compliance_agents_tasks()
            compliance_monitor_task = tasks.compliance_monitor_task(compliance_monitor_agent)

            crew = Crew(agents=[compliance_monitor_agent], 
                           tasks=[compliance_monitor_task], 
#                          process=Process.sequential, 
                           verbose=False)

            # Perform compliance monitoring
            output = crew.kickoff(inputs={'text': text, 'compliance_structure': compliance_structure})
            output_string = output.raw
            output_dict = extract_compliance_issues(output_string)

            if output_dict:
                customer_dict, agent_dict = split_compliance_issues(output_dict)
                customer_issues = format_compliance_issues(customer_dict)
                recovery_agent_issues = format_compliance_issues(agent_dict)

                # Display results
                st.subheader("Detected Compliance Violations by Customer")
                st.text(customer_issues if customer_issues else "No compliance violations detected for the customer.")
                st.subheader("Detected Non-Compliance Violations by Recovery Agent")
                st.text(recovery_agent_issues if recovery_agent_issues else "No compliance violations detected for the recovery agent.")
            else:
                st.error("No compliance issues detected or there was an error in processing.")
        else:
            st.warning("Please enter some text to analyze.")

if __name__ == "__main__":
    main()
