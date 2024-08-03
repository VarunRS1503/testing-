import re
import json

def extract_compliance_issues(text):
    pattern = re.compile(r'\{.*\}', re.DOTALL)
    match = pattern.search(text)
    if match:
        dictionary_text = match.group(0)
        compliance_issues = json.loads(dictionary_text)
        return compliance_issues
    else:
        return None

def format_compliance_issues(compliance_data):
    formatted_issues = ""
    issues = compliance_data.get("compliance_issues", [])
    for i, issue in enumerate(issues, start=1):
        issue_text = f"{i}. issue_occurred: {issue['issue_occurred']}\nconversation_part: {issue['conversation_part']}\n"
        formatted_issues += issue_text + "\n"
    return formatted_issues.strip()

def split_compliance_issues(output_dict):
    customer_dict = {'compliance_issues': []}
    agent_dict = {'compliance_issues': []}
    for issue in output_dict['compliance_issues']:
        if issue['conversation_part'].lower().startswith('customer'):
            customer_dict['compliance_issues'].append(issue)
        elif issue['conversation_part'].lower().startswith('recovery_agent'):
            agent_dict['compliance_issues'].append(issue)
    return customer_dict, agent_dict
