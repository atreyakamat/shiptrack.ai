import { motion } from 'framer-motion';

const Footer = () => {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="relative z-10 py-12 px-6 border-t border-white/[0.06]"
    >
      <div className="max-w-7xl mx-auto text-center">
        <p
          className="text-[#F8FAFC] font-semibold text-lg mb-2"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          ShipTrack AI
        </p>
        <p
          className="text-[#94A3B8] text-sm mb-1"
          style={{ fontFamily: "'Inter', sans-serif" }}
        >
          Built with Python &bull; Flask &bull; Streamlit &bull; OCR &bull; AI
        </p>
        <p
          className="text-[#94A3B8]/60 text-xs"
          style={{ fontFamily: "'Inter', sans-serif" }}
        >
          Designed & Developed by Atreya Kamat
        </p>
      </div>
    </motion.footer>
  );
};

export default Footer;
