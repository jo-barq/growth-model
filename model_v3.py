import streamlit as st
import plotly.express as px
import random
import pandas as pd
import base64

class User:
    def __init__(self, profile):
        self.profile = profile
        self.invites_left = 3
        self.connections = []
        self.age = 0  # Add this line

    def invite(self, other):
        if self.invites_left > 0:
            self.connections.append(other)
            self.invites_left -= 1
            other.connections.append(self)

def simulate_one_period(users, invite_limit, sybil_to_sybil, honest_to_sybil):
    new_users = []
    for user in users:
        user.age += 1  # Increment the age of the user
        if user.invites_left > 0 and len(user.connections) < invite_limit:
            if user.profile == "sybil":
                # Invite as many users as possible in the next period
                for _ in range(user.invites_left):
                    new_profile = "sybil" if random.random() < sybil_to_sybil else "honest"
                    new_user = User(new_profile)
                    user.invite(new_user)
                    new_users.append(new_user)
            else:
                # Invite one user every two periods until their invites run out
                if user.age % 2 == 0:
                    new_profile = "sybil" if random.random() < honest_to_sybil else "honest"
                    new_user = User(new_profile)
                    user.invite(new_user)
                    new_users.append(new_user)
    return users + new_users

    

def main():
    st.sidebar.header('Parameters')
    num_periods = st.sidebar.slider('Number of periods', min_value=1, max_value=100, value=10)
    num_initial_users = st.sidebar.slider('Initial number of users', min_value=1, max_value=1000, value=100)
    initial_sybil_percentage = st.sidebar.slider('Percentage of initial sybil users', min_value=0.0, max_value=1.0, value=0.5)
    invite_limit = st.sidebar.slider('Invite limit', min_value=0, max_value=10, value=3)
    sybil_to_sybil = st.sidebar.slider('Sybil-to-sybil probability', min_value=0.0, max_value=1.0, value=0.8)
    honest_to_sybil = st.sidebar.slider('Honest-to-sybil probability', min_value=0.0, max_value=1.0, value=0.2)

    users = [User("sybil") if random.random() < initial_sybil_percentage else User("honest") for _ in range(num_initial_users)]
    data = []

    for i in range(num_periods):
        users = simulate_one_period(users, invite_limit, sybil_to_sybil, honest_to_sybil)
        data.append({"period": i, "sybil": sum(user.profile == "sybil" for user in users), 
                     "honest": sum(user.profile == "honest" for user in users), 
                     "total": len(users)})

    df = pd.DataFrame(data).set_index('period')
    df.to_csv('simulation.csv')

    # Transform the data to represent proportions
    df_percentage = df[['sybil', 'honest']].div(df['total'], axis=0)

    # Create and display a stacked area chart
    area_fig = px.area(df_percentage.reset_index().melt(id_vars='period'), 
                       x='period', y='value', color='variable', 
                       labels={'value': 'Proportion', 'variable': 'User Type'},
                       title='Proportion of User Types Over Time')
    st.plotly_chart(area_fig)

    # Create and display a bar plot of the data
    bar_fig = px.bar(df.reset_index().melt(id_vars='period', value_vars=['sybil', 'honest']), 
                     x='period', y='value', 
                     color='variable', title='User Comparison Over Time',
                     labels={'value': 'User Count', 'variable': 'User Type'})
    st.plotly_chart(bar_fig)

    # Create and display a pie chart for the last period
    last_period = df.iloc[-1]
    pie_fig = px.pie(names=['Sybil Users', 'Honest Users'], values=[last_period['sybil'], last_period['honest']], 
                     title='User Proportions in Final Period')
    st.plotly_chart(pie_fig)

    # Add a button for downloading the CSV file
    if st.button('Download CSV File'):
        b64 = base64.b64encode(df.to_csv(index=False).encode()).decode()  # some strings
        href = f'<a href="data:file/csv;base64,{b64}" download="simulation.csv">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
        st.markdown(href, unsafe_allow_html=True)

main()
