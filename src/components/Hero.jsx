import { motion } from 'framer-motion';
import { useState } from 'react';

const Hero = () => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    setStatus('submitting');
    try {
      const formData = new URLSearchParams();
      formData.append('email', email);

      const res = await fetch(`https://waitlister.me/s/${import.meta.env.VITE_WAITLIST_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString()
      });

      if (res.ok) {
        setStatus('success');
        setEmail('');
      } else {
        setStatus('error');
      }
    } catch (err) {
      setStatus('error');
    }
  };

  const scrollToWishlist = () => {
    document.getElementById('wishlist')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-center">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="mb-8"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium text-[#38BDF8] bg-[#0F172A]/60 border border-[#38BDF8]/20 backdrop-blur-sm">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#38BDF8] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#38BDF8]"></span>
          </span>
          Coming Soon
        </span>
      </motion.div>

      {/* Main Heading */}
      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.4 }}
        className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-[#F8FAFC] mb-6"
        style={{ fontFamily: "'Space Grotesk', sans-serif", textShadow: '0 0 80px rgba(56, 189, 248, 0.15)' }}
      >
        ShipTrack AI
      </motion.h1>

      {/* Subheading */}
      <motion.p
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.6 }}
        className="text-lg md:text-xl text-[#94A3B8] max-w-2xl mb-12 leading-relaxed"
        style={{ fontFamily: "'Inter', sans-serif" }}
      >
        An Intelligent Shipment Management Platform built for individuals, creators, and businesses. Track smarter. Understand deliveries. Organize everything.
      </motion.p>

      {/* Waitlist Form */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.8 }}
        className="w-full max-w-md mx-auto mb-16"
      >
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              required
              disabled={status === 'submitting' || status === 'success'}
              className="flex-1 px-5 py-3.5 bg-[#0F172A]/80 border border-white/10 rounded-xl text-[#F8FAFC] placeholder:text-[#94A3B8] focus:outline-none focus:border-[#38BDF8]/50 focus:ring-1 focus:ring-[#38BDF8]/50 backdrop-blur-sm transition-all disabled:opacity-50"
            />
            <motion.button
              whileHover={status !== 'submitting' && status !== 'success' ? { scale: 1.02 } : {}}
              whileTap={status !== 'submitting' && status !== 'success' ? { scale: 0.98 } : {}}
              disabled={status === 'submitting' || status === 'success'}
              type="submit"
              className="px-8 py-3.5 bg-[#38BDF8] text-[#020617] font-semibold rounded-xl text-base hover:bg-[#7DD3FC] transition-colors duration-300 shadow-lg shadow-[#38BDF8]/20 disabled:opacity-70 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {status === 'submitting' ? 'Joining...' : status === 'success' ? 'Joined!' : 'Join Waitlist'}
            </motion.button>
          </div>
          
          <div className="min-h-[24px] text-sm flex items-center justify-center">
            {status === 'success' && (
              <span className="text-emerald-400 font-medium">You're on the list! We'll be in touch soon.</span>
            )}
            {status === 'error' && (
              <span className="text-red-400 font-medium">Oops, something went wrong. Please try again.</span>
            )}
            {status === 'idle' && (
              <button 
                type="button" 
                onClick={scrollToWishlist}
                className="text-[#94A3B8] hover:text-[#F8FAFC] transition-colors underline decoration-white/20 underline-offset-4"
              >
                Or scroll down to view features
              </button>
            )}
          </div>
        </form>
      </motion.div>

      {/* Developer Signature */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1.0 }}
        className="flex flex-col items-center gap-1"
      >
        <span className="text-sm text-[#94A3B8]" style={{ fontFamily: "'Inter', sans-serif" }}>
          Designed & Developed by
        </span>
        <span
          className="text-base font-semibold bg-clip-text text-transparent"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            backgroundImage: 'linear-gradient(90deg, #38BDF8, #818CF8, #C084FC, #38BDF8)',
            backgroundSize: '200% auto',
            animation: 'gradientShift 3s linear infinite',
          }}
        >
          Atreya Kamat
        </span>
      </motion.div>
    </section>
  );
};

export default Hero;
