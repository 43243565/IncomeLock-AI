if st.session_state.page == "Splash":
    st.markdown("""
    <div class="splash">
        <div class="splash-logo">🛡️</div>
        <div class="splash-title">IncomeLock AI</div>
        <div class="splash-subtitle">
            Parametric income protection for gig workers
        </div>
        <div class="card" style="text-align:left;">
            <b>What this app covers:</b><br><br>
            • Registration process<br>
            • Insurance policy management<br>
            • Dynamic premium calculation<br>
            • 10-year actuarial engine<br>
            • Hyperlocal risk mapping<br>
            • Stress testing<br>
            • Claims management<br>
            • Fraud verification<br>
            • Instant settlement simulation
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get Started"):
        set_page("Registration")
        st.rerun()