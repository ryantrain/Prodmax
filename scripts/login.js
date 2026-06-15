const spinner = document.getElementById('spinner');

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
           
            const response_dashboard = await fetch('http://localhost:8000/api/dashboard', {
                method: 'POST'
            });

            const dashboardData = await response_dashboard.json();

            sessionStorage.setItem('preFetchedData', JSON.stringify(dashboardData));

            window.location.href = 'dashboard.html';

        } else {
            document.getElementById('invalid-login').toggleAttribute('hidden');
            console.log(data.message);
        }

    } catch (error) {
        console.error('Error during login:', error);
    }

});