const spinner = document.getElementById('spinner');
const { supabase } = require('../scripts/supabaseClient.js');

document.getElementById('login-form').addEventListener('submit', async(e) => {
    e.preventDefault();

    try {
        
        spinner.classList.toggle('hidden');

        const formData = new FormData(e.target);

        const response = await fetch('http://localhost:8000/api/login', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.message === 'Login successful') {

            await supabase.auth.signInWithPassword({
                email: formData.get('email'),
                password: formData.get('password')
            });
           
            const response_dashboard = await fetch('http://localhost:8000/api/dashboard', {
                method: 'POST'
            });

            const response_navbar = await fetch('http://localhost:8000/api/navbar', {
                method: 'POST'
            });

            const dashboardData = await response_dashboard.json();
            const navbarData = await response_navbar.json();

            sessionStorage.setItem('preFetchedData', JSON.stringify({ ...dashboardData, ...navbarData }));

            window.location.href = 'dashboard.html';

        } else {
            document.getElementById('invalid-login').toggleAttribute('hidden');
        }

    } catch (error) {
        console.error('Error during login:', error);
    }

});