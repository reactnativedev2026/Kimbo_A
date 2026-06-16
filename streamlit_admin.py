# import os
# import streamlit as st
# import requests
# from typing import List, Dict
# 
# # Base URL of the FastAPI backend (adjust if needed)
# BASE_URL = os.getenv("API_BASE_URL", "https://sbbms-new.onrender.com")
# 
# # ---------- Helper functions ----------
# def api_post(endpoint: str, json: dict, token: str = None):
#     headers = {"Authorization": f"Bearer {token}"} if token else {}
#     response = requests.post(f"{BASE_URL}{endpoint}", json=json, headers=headers)
#     response.raise_for_status()
#     return response.json()
# 
# def api_patch(endpoint: str, params: dict = None, json: dict = None, token: str = None):
#     headers = {"Authorization": f"Bearer {token}"} if token else {}
#     response = requests.patch(f"{BASE_URL}{endpoint}", params=params, json=json, headers=headers)
#     response.raise_for_status()
#     return response.json()
# 
# def api_get(endpoint: str, token: str = None):
#     headers = {"Authorization": f"Bearer {token}"} if token else {}
#     response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
#     response.raise_for_status()
#     return response.json()
# 
# # ---------- Streamlit UI ----------
# st.set_page_config(page_title="Admin Dashboard", layout="centered")
# st.title("🏢 Admin Dashboard – Building Material Reward Management")
# 
# if "token" not in st.session_state:
#     st.session_state.token = None
#     st.session_state.role = None
# 
# # ---- Login ----
# if not st.session_state.token:
#     with st.form(key="login_form"):
#         st.subheader("🔐 Admin Login")
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")
#         submitted = st.form_submit_button("Login")
#         if submitted:
#             try:
#                 data = api_post("/users/auth/login", {"email": email, "password": password})
#                 st.session_state.token = data["access_token"]
#                 st.session_state.role = data["user_data"]["role"]
#                 st.success(f"Logged in as {st.session_state.role}")
#             except Exception as e:
#                 st.error(f"Login failed: {e}")
#     st.stop()
# 
# # Guard: only admins allowed to see the admin sections
# if not st.session_state.role or st.session_state.role.upper() != "ADMIN":
#     st.warning("You are logged in as a non‑admin user. Access denied.")
#     st.stop()
# 
# # ---- Sidebar navigation ----
# section = st.sidebar.radio("Navigate", [
#     "🏠 Home",
#     "👥 Contractors",
#     "📦 Purchases (Approve)",
#     "💎 Add Points",
#     "🛠️ Add Contractor",
# ])
# 
# # ---- Home ----
# if section == "🏠 Home":
#     st.header("Welcome, Admin!")
#     st.write("Use the sidebar to manage contractors, approve purchases, and adjust token balances.")
# 
# # ---- Contractors list ----
# elif section == "👥 Contractors":
#     st.header("📋 Contractor List")
#     try:
#         contractors = api_get("/users/admin/contractors", token=st.session_state.token)
#         if contractors["status"] == "success":
#             for c in contractors["user_data"]:
#                 st.markdown(f"- **{c['name']}** – {c['email']} – Tokens: {c.get('total_tokens', 0)}")
#         else:
#             st.warning("No contractors found.")
#     except Exception as e:
#         st.error(f"Failed to fetch contractors: {e}")
# 
# # ---- Add Contractor ----
# elif section == "🛠️ Add Contractor":
#     st.header("➕ Add New Contractor")
#     with st.form(key="add_contractor_form"):
#         name = st.text_input("Name")
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")
#         submitted = st.form_submit_button("Create Contractor")
#         if submitted:
#             try:
#                 payload = {"name": name, "email": email, "password": password}
#                 res = api_post("/users/admin/add-contractor", payload, token=st.session_state.token)
#                 st.success(res["message"])
#             except Exception as e:
#                 st.error(f"Error adding contractor: {e}")
# 
# # ---- Approve Purchases ----
# elif section == "📦 Purchases (Approve)":
#     st.header("🗂️ Pending Purchases")
#     # Assuming an endpoint that lists pending purchases exists (you may need to create one).
#     try:
#         pending = api_get("/purchases/pending", token=st.session_state.token)
#         for p in pending.get("data", []):
#             with st.expander(f"Purchase #{p['id']} – {p['product_name']}"):
#                 st.json(p)
#                 if st.button("Approve", key=f"approve_{p['id']}"):
#                     try:
#                         api_patch(f"/purchases/admin/{p['id']}/status", params={"status": "approved"}, token=st.session_state.token)
#                         st.success("Purchase approved and tokens allocated.")
#                     except Exception as e:
#                         st.error(f"Approval failed: {e}")
#     except Exception as e:
#         st.warning("No pending purchases endpoint yet or request failed.")
#         st.info(str(e))
# 
# # ---- Add Points ----
# elif section == "💎 Add Points":
#     st.header("🔧 Manually Add Points to Contractor")
#     with st.form(key="add_points_form"):
#         contractor_id = st.number_input("Contractor ID", min_value=1, step=1)
#         points = st.number_input("Points to add", min_value=1, step=1)
#         submitted = st.form_submit_button("Add Points")
#         if submitted:
#             try:
#                 payload = {"points": points}
#                 res = api_post(f"/users/admin/contractors/{int(contractor_id)}/add-points", payload, token=st.session_state.token)
#                 st.success(res["message"])
#             except Exception as e:
#                 st.error(f"Failed to add points: {e}")
# 
# # ---- Logout ----
# if st.button("🚪 Logout"):
#     st.session_state.clear()
#     st.experimental_rerun()
