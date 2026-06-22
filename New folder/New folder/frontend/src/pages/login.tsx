import { useNavigate } from "react-router-dom";
import bg from '../assets/bg-1.png'
import person from '../assets/person.png'
import '../App.css'

function Login() {
    const navigate = useNavigate();


    const handleLogin = async () => {
        const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement;
        const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement;

        const email = emailInput?.value;
        const password = passwordInput?.value;

        if (!email || !password) {
            alert("Enter email and password");
            return;
        }

        try {
            const res = await fetch("http://localhost:5001/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (res.ok) {
                localStorage.setItem("userEmail", email);
                navigate("/form");
            } else {
                alert(data.message);
            }

        } catch (error) {
            console.error(error);
            alert("Server error");
        }
    };

    return (
        <>
            <section className='column  image  w-screen h-screen item-center justify-center ' style={{ backgroundImage: `url(${bg})` }}>
                <form action="" className='bg-white w-fit p-9  column g-5 r-1 ab relative '>
                    <div className="w-100p row justify-center">
                        <div className='w-6 h-6 circle image border absolute  profile' style={{ backgroundImage: `url(${person})` }}> </div>
                    </div>

                    <div className='column g-3 text-center' >
                        <h2>Sign In</h2>
                        <p>Sign In to access form</p>
                    </div>

                    <div className='column g-1'>
                        <label htmlFor="Email"><h5>Email</h5></label>
                        <input className='w-28 h-2.5 p-2 r-1 outline-none border shadow ' type="email" placeholder='example@gmail.com' />
                    </div>

                    <div className='column g-1 '>
                        <label htmlFor="password"><h5>Password</h5></label>
                        <input className='w-28 h-2.5 p-2 r-1 outline-none border shadow column ' type="password" placeholder='••••••••.' />
                    </div>

                    <div className='pointer'>
                        <p>Froget password?</p>
                    </div>

                    <div>
                        <button
                            type="button"
                            className="w-28 p-3 r-1 border-none bg-primary text-white pointer"
                            onClick={handleLogin}
                        >
                            SIGN IN
                        </button>
                    </div>

                    <div className="text-center">
                        <p>
                            Dont have an account?{" "}
                            <span
                                className="pointer text-primary"
                                onClick={() => navigate("/signup")}
                            >
                                <b>Go to Signup</b>
                            </span>
                        </p>
                    </div>
                </form>
            </section>
        </>
    )
}

export default Login;