import streamlit as st
import pandas as pd

# Load the allocations CSV (uploaded file)
allocations_df = pd.read_csv("/home/user/student_college_allocations_system.csv")

# Streamlit Dashboard UI
st.set_page_config(page_title="🎓 Student College Allocation Dashboard", layout="centered")

st.title("🎓 Student College Allocation System")
st.write("Enter your **UniqueID** below to check your college allocation.")

# Input box for UniqueID
unique_id = st.text_input("🔑 Enter Your UniqueID:")

if unique_id:
    try:
        # Convert to int if IDs are numeric
        uid = int(unique_id)
        result = allocations_df[allocations_df["UniqueID"] == uid]

        if not result.empty:
            st.success("✅ Allocation Found!")
            
            # Show details in a nice card/table
            st.subheader("📋 Allocation Details")
            st.dataframe(result)

            # Highlight main result
            st.info(f"🏫 You have been allocated to **{result.iloc[0]['CollegeID']}**")

            # Optionally download allocation result
            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Your Allocation Result",
                data=csv,
                file_name=f"allocation_{uid}.csv",
                mime="text/csv",
            )
        else:
            st.error("❌ No allocation found for this UniqueID. Please try again.")
    except ValueError:
        st.warning("⚠️ Please enter a valid numeric UniqueID.")
else:
    st.info("ℹ️ Please enter your UniqueID above to search.")

# Footer
st.markdown("---")
st.caption("Developed with ❤️ using Streamlit")

