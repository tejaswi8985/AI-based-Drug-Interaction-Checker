import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/login";
import Form from "./pages/form";
import Signup from "./pages/signup";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/form" element={<Form />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

// // import { useState } from 'react'
// import { useEffect } from "react";
// import bg from './assets/bg-1.png'
// import person from './assets/person.png'
// import './App.css'

// function App() {
//     useEffect(() => {
//     const networkLink = `${window.location.protocol}//${window.location.host}`;
//     console.log("Network Link:", networkLink);
//   }, []);

//   return (
//     <>
    
//     <section className='column  image  w-screen h-screen item-center justify-center ' style={{ backgroundImage: `url(${bg})` }}>
//       <form action="" className='bg-white w-fit p-9  column g-5 r-1 ab relative '>
//         <div className="w-100p row justify-center">
//           <div className='w-6 h-6 circle image border absolute  profile' style={{ backgroundImage: `url(${person})` }}> </div>
//         </div>

//       <div className='column g-3 text-center' >
//         <h2>Sign In</h2>
//         <p>Sign In to access form</p>
//       </div>

//       <div className='column g-1'>
//         <label htmlFor="Email"><h5>Email</h5></label>
//         <input className='w-28 h-2.5 p-2 r-1 outline-none border shadow ' type="mail" placeholder='example@gmail.com' />
//       </div>

//       <div className='column g-1 '>
//         <label htmlFor="Email"><h5>Password</h5></label>
//         <input className='w-28 h-2.5 p-2 r-1 outline-none border shadow' type="password" placeholder='password' />
//       </div>

//       <div className='pointer'>
//         <p>Froget password?</p>
//       </div>

//       <div>
//         <button className='w-28 p-3 r-1 border-none bg-primary text-white pointer'>SIGN IN</button>
//       </div>

//       <div className='text-center'>
//         <p>Dont have an account? <b className='pointer'>Sign up</b> </p>
//       </div>
//       </form>
//     </section>

//       <section className='h-full w-full px-8 py-11 bg-primary-light g-8 column '>

//         <div className='text-center column g-4'>
//           <h1 className='text-primary-dark'>Ayurvedic-Allopathic Drug Interaction Checker</h1>
//           <h2 className='text-gray'>Search possible herb-drug interactions</h2>
//         </div>

//         <form action="" className='column  g-6 desktop'>

//           <div className='shadow border column g-5 p-8 w-100p r-1 bg-white px-8'>
//             <div className='text-primary-dark-2'>
//               <h2 className='border-bottom pb-1'>Search Interaction</h2>
//             </div>

//             <div className='row flex-wrap g-7'>

//               <div className='column g-3 grow shrink input-container'>
//                 <label htmlFor="Herb"><p>Ayurvedic / Herb Name</p></label>
//                 <input className='w-full h-2.5 p-2 r-1 outline-none shadow border' type="text" placeholder='e.g. Amla, Ajamoda, Ashwagandha' />
//               </div>

//               <div className='column g-3 grow shrink input-container'>
//                 <label htmlFor="Drug"><p>Allopathic Drug Name</p></label>
//                 <input className='w-full h-2.5 p-2 r-1 outline-none shadow border' type="text" placeholder='e.g. Aspirin, Lithium, Metformin' />
//               </div>

//               <div className='column g-3 grow shrink input-container'>
//                 <label htmlFor="Severity"><p>Severity Filter <span className='text-gray'>(Optional)</span></p></label>
//                 <select className='w-full h-2.5 p-2 r-1 outline-none shadow border'>
//                   <option value=""> All Severities </option>
//                   <option value=""> All Severities </option>
//                   <option value=""> All Severities </option>
//                   <option value=""> All Severities </option>
//                   <option value=""> All Severities </option>
//                 </select>
//               </div>

//               <div className='grow row shrink justify-end input-container'>
//                 <button className='w-50p h-3 bg-primary text-white pointer border-none r-2'> Check Interaction </button>
//               </div>

//             </div>
//           </div>

//           <div className=' column border shadow g-5 p-8 w-100p r-1 bg-white'>
//             <div className='text-primary-dark-2'>
//               <h2 className='border-bottom pb-1 '>Search Result</h2>
//             </div>
//             <div className='shadow border r-1 '>
//               <div className='border-bottom p-5 column g-3'>
//                 <h2 className='text-primary-dark-2 '>Amalaki (Amla)</h2>
//                 <p> System: Ayurveda <span className='text-gray'> | Source: </span> <span className='text-primary-light'> WebMD </span>   </p>
//               </div>
//               <div className='p-5 '>
//                 <div className='border shadow r-1'>
//                   <div className=' p-3 border-bottom row justify-between'>
//                     <h3 className='text-gray'>Aspirin</h3>
//                     <button className='h-2.5 w-8 border-none bg-button text-white r-2'> <h3>Moderate</h3></button>
//                   </div>
//                   <div className='p-3 column g-3'>
//                     <span className='row g-1'><p> <b className='text-primary-dark-2'>Mechanism :</b><span> Additive blood-thinning effect</span></p></span>
//                     <span className='row g-1'><p> <b className='text-primary-dark-2'>Clinical Effect :</b><span> Increased bleeding risk.</span></p></span>
//                     <span className='row g-1'><p> <b className='text-primary-dark-2'>Recommendation :</b><span> Use cautiously. Monitor for bruisiuiicing or bleeding.</span></p></span>
//                   </div>
//                 </div>
//               </div>
//             </div>
//           </div>

//           <div className=' shadow border column g-5 p-8 w-100p r-1 bg-white   '>
//             <div >
//               <h2 className='border-bottom pb-1 '>Recent Searches:</h2>
//             </div>
//             <div className='column g-2'>
//               <div className='row g-2'>
//                 <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#4e5b7b"><path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z" /></svg>
//                 <a href="#" className="text-none"><p className='border-bottom pe-5 pb-2 text-primary'>Amla + Aspirin</p></a> 
//               </div>
//               <div className='row g-2'>
//                 <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#4e5b7b"><path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z" /></svg>
//                 <a href="#" className="text-none"> <p className='border-bottom pe-5 pb-2 text-primary'>Ajamoda + Lithium</p></a>
//               </div>
//               <div className='row g-2'>
//                 <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#4e5b7b"><path d="M504-480 320-664l56-56 240 240-240 240-56-56 184-184Z" /></svg>
//                 <a href="" className="text-none"> <p className='pe-5  text-primary'>Celery + Venlafaxine</p></a>
//               </div>
//             </div>
//           </div>

//         </form>

//         <div className='text-center  desktop'>
//           <p className='text-gray '>For academic and informational use only. Consult your healthcare provider for professional advice.</p>
//         </div>

//       </section>

//     </>
//   )
// }

// export default App;
