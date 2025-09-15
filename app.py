import streamlit as st
import time  # For fake reminders

# Fake client data (simulates Lawmatics pull)
clients = {
    "Dover": {
        "details": "Mr. & Mrs. Dover - Last: 7/2 Vision Meeting with Thad (Intake Specialist)",
        "analysis_status": "80% done, missing asset list"
    },
    "McKrackin": {
        "details": "Mr. & Mrs. McKrackin - Mother's plan from 2017 (Phillys passed 6 months ago)",
        "mother_plan": "Will exists, assets >$50K - Probate likely needed"
    },
    "Jass": {
        "details": "Mr. Jass - Medicaid application active",
        "hhs_notes": "Last Iowa HHS update 8/15/25 - No changes on spousal nursing home bills. Suggest appeal Form 470-0661"
    }
}

# Roles and who can see what
roles = {
    "Receptionist": {"can_start": True, "can_respond": False, "delegates_to": []},
    "Attorney": {"can_start": False, "can_respond": True, "delegates_to": ["Intake Specialist", "Probate Paralegal", "Medicaid Consultant"]},
    "Intake Specialist": {"can_start": True, "can_respond": True, "delegates_to": []},
    "Medicaid Consultant": {"can_start": False, "can_respond": True, "delegates_to": []},
    "Probate Paralegal": {"can_start": False, "can_respond": True, "delegates_to": []},
    "Executive Assistant": {"can_start": True, "can_respond": True, "delegates_to": []},
    "Office Manager": {"can_start": True, "can_respond": True, "delegates_to": []}  # Full access
}

# Session state for pending calls (like a shared notebook)
if "pending_calls" not in st.session_state:
    st.session_state.pending_calls = []  # List of dicts: {'client': , 'question': , 'status': 'pending', 'response': None, 'delegated_to': None}
if "reminders" not in st.session_state:
    st.session_state.reminders = []  # For delays

# AI Suggestion function (simple rules based on your examples)
def get_ai_suggestion(client, question):
    client_lower = client.lower()
    question_lower = question.lower()
    if "dover" in client_lower and "design meeting" in question_lower:
        return f"Analysis: {clients['Dover']['analysis_status']}. Options: 1) Finished—schedule now. 2) Not finished—schedule in 2 weeks. 3) Wait for missing info (e.g., asset list)."
    elif "mckrackin" in client_lower and "probate" in question_lower:
        return f"Based on mom's {clients['McKrackin']['mother_plan']}. Next: Open probate if assets qualify—file Form 706. Delegate to Probate Paralegal?"
    elif "jass" in client_lower and ("medicaid" in question_lower or "bill" in question_lower):
        return f"{clients['Jass']['hhs_notes']}. Suggest: Appeal the bill or call HHS. Delegate to Medicaid Consultant."
    else:
        return "Review client file. General response: 'We'll look into this and get back to you soon.'"

# Title
st.title("Estate Planning Call Hub - Prototype")
st.write("Simulates client calls. Test your examples: Dover (Design Mtg), McKrackin (Probate), Jass (Medicaid Bill).")

# Sidebar: Role selector
selected_role = st.sidebar.selectbox("Select Your Role", list(roles.keys()))
st.sidebar.write("Switch roles to see different views.")

# Role-based views
if roles[selected_role]["can_start"]:
    st.header(f"{selected_role} Dashboard")
    # New Call Section
    with st.expander("Start New Call"):
        client_name = st.text_input("Client Name (e.g., Dover, McKrackin, Jass)")
        question = st.text_area("Client's Question", placeholder="E.g., When's our Design Meeting?")
        if st.button("Submit Call") and client_name and question:
            if client_name in clients:
                suggestion = get_ai_suggestion(client_name, question)
                new_call = {
                    "client": client_name,
                    "details": clients[client_name]["details"],
                    "question": question,
                    "ai_suggestion": suggestion,
                    "status": "pending",
                    "response": None,
                    "delegated_to": None,
                    "timestamp": time.time()
                }
                st.session_state.pending_calls.append(new_call)
                st.success(f"Call submitted for {client_name}! Attorney/Expert notified.")
                st.rerun()
            else:
                st.error("Client not found—try one of the examples.")

# Pending Calls View (for responders) - FIXED: Now shows delegated calls to the right person
if roles[selected_role]["can_respond"]:
    st.header(f"{selected_role} - Pending Calls")
    # Filter visible calls: pending for all, OR delegated specifically to this role
    visible_calls = [
        call for call in st.session_state.pending_calls 
        if call["status"] == "pending" or 
           (call["status"] == "delegated" and call["delegated_to"] == selected_role)
    ]
    if not visible_calls:
        st.info("No pending calls for you—have someone start one or delegate here!")
    else:
        for i, call in enumerate(visible_calls):
            prefix = "Delegated to you: " if call["status"] == "delegated" else ""
            with st.expander(f"{prefix}{call['client']} - {call['question'][:50]}..."):
                st.write(f"**Details:** {call['details']}")
                st.write(f"**AI Suggestion:** {call['ai_suggestion']}")
                
                # Response options (same for all responders)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Option 1: Ready/Schedule Now", key=f"opt1_{i}"):
                        call["response"] = "Great news! Your Design Meeting is ready—let's schedule for next week."
                        call["status"] = "done"  # Direct to done, since handled
                        st.rerun()
                with col2:
                    if st.button(f"Option 2: In 2 Weeks", key=f"opt2_{i}"):
                        call["response"] = "Not quite ready, but we can schedule your meeting in 2 weeks."
                        call["status"] = "done"
                        st.rerun()
                with col3:
                    if st.button("Custom Response", key=f"custom_{i}"):
                        custom_resp = st.text_input("Your response:", key=f"custom_input_{i}")
                        if st.button("Send Custom", key=f"send_custom_{i}"):
                            call["response"] = custom_resp
                            call["status"] = "done"
                            st.rerun()
                
                # Delegate (only if this role can)
                if roles[selected_role]["delegates_to"]:
                    delegate_to = st.selectbox("Or Delegate To:", ["None"] + roles[selected_role]["delegates_to"], key=f"delegate_{i}")
                    if delegate_to != "None" and st.button("Delegate", key=f"delegate_btn_{i}"):
                        call["delegated_to"] = delegate_to
                        call["status"] = "delegated"
                        st.success(f"Delegated to {delegate_to}!")
                        st.rerun()
                
                # Mark Done (loops back to receptionist)
                if st.button("Mark Done & Notify Receptionist", key=f"done_{i}"):
                    call["status"] = "done"
                    st.success(f"Response sent: '{call['response'] or 'Handled!'}' Receptionist can now call back.")
                    st.rerun()

# Receptionist Response View
if selected_role == "Receptionist":
    st.header("Your Responses")
    responded_calls = [call for call in st.session_state.pending_calls if call["status"] == "done"]
    if responded_calls:
        for call in responded_calls:
            st.write(f"**{call['client']}:** {call['response']}")
            if st.button("Call Client Back", key=f"call_back_{call['client']}"):
                st.balloons()  # Fun confetti!
                st.success("Call logged—great job!")
    else:
        st.info("Waiting for responses...")

# Reminders (for delays >1 min in demo) - Updated to include delegated
st.header("Reminders (Auto-Nags)")
reminder_calls = [
    call for call in st.session_state.pending_calls 
    if (call["status"] == "pending" or 
        (call["status"] == "delegated" and call["delegated_to"] == selected_role)) and 
       (time.time() - call["timestamp"] > 60)
]
for call in reminder_calls:
    st.warning(f"Nudge: {call['client']} - {call['question'][:30]}... Finish by EOD? Suggested: {call['ai_suggestion'][:50]}")
    if st.button("Quick Mark Done", key=f"quick_{call['client']}"):
        call["status"] = "done"
        call["response"] = "Follow-up completed."
        st.rerun()

# Office Manager Full View
if selected_role == "Office Manager":
    st.header("All Open Tasks")
    open_calls = [call for call in st.session_state.pending_calls if call["status"] != "done"]
    for call in open_calls:
        st.write(f"- {call['client']}: {call['question']} (Status: {call['status']}, Delegated: {call['delegated_to']})")

# Footer
st.write("---")
st.write("*Prototype v1.1 - Delegation fixed! Next: Real Lawmatics connect + more clients.*")
