import { motion } from 'framer-motion';

const wishlistItems = [
  { icon: '📦', title: 'Shipment Dashboard', description: 'Manage all shipments from one place.', status: 'In Progress' },
  { icon: '📮', title: 'India Post Tracking', description: 'Track India Post consignments with complete routing history.', status: 'In Progress' },
  { icon: '📈', title: 'Delivery Analytics', description: 'View delivery trends, transit duration and shipment insights.', status: 'Planned' },
  { icon: '📸', title: 'OCR Receipt Scanner', description: 'Upload India Post receipts and automatically extract tracking numbers.', status: 'Planned' },
  { icon: '🤖', title: 'AI Shipment Summaries', description: 'Generate intelligent summaries of shipment journeys and delays.', status: 'Research' },
  { icon: '💬', title: 'WhatsApp Notifications', description: 'Receive shipment updates directly on WhatsApp Business.', status: 'Future' },
  { icon: '📂', title: 'Shipment History', description: 'Maintain a searchable archive of every shipment you\'ve tracked.', status: 'Planned' },
  { icon: '🚚', title: 'Multi Courier Support', description: 'Support India Post, DTDC, Blue Dart, Delhivery and more.', status: 'Future' },
  { icon: '🧠', title: 'Smart Predictions', description: 'Predict delivery dates and detect delays using AI.', status: 'Research' },
  { icon: '📊', title: 'Interactive Dashboard', description: 'Beautiful analytics with charts and insights.', status: 'Planned' },
];

const getStatusStyles = (status) => {
  switch (status) {
    case 'In Progress':
      return 'bg-[#38BDF8]/10 text-[#38BDF8] border-[#38BDF8]/20';
    case 'Planned':
      return 'bg-[#818CF8]/10 text-[#818CF8] border-[#818CF8]/20';
    case 'Research':
      return 'bg-[#FBBF24]/10 text-[#FBBF24] border-[#FBBF24]/20';
    case 'Future':
      return 'bg-[#C084FC]/10 text-[#C084FC] border-[#C084FC]/20';
    default:
      return 'bg-[#38BDF8]/10 text-[#38BDF8] border-[#38BDF8]/20';
  }
};

const getGlowColor = (status) => {
  switch (status) {
    case 'In Progress': return 'rgba(56, 189, 248, 0.12)';
    case 'Planned': return 'rgba(129, 140, 248, 0.12)';
    case 'Research': return 'rgba(251, 191, 36, 0.12)';
    case 'Future': return 'rgba(192, 132, 252, 0.12)';
    default: return 'rgba(56, 189, 248, 0.12)';
  }
};

const getBorderColor = (status) => {
  switch (status) {
    case 'In Progress': return 'rgba(56, 189, 248, 0.3)';
    case 'Planned': return 'rgba(129, 140, 248, 0.3)';
    case 'Research': return 'rgba(251, 191, 36, 0.3)';
    case 'Future': return 'rgba(192, 132, 252, 0.3)';
    default: return 'rgba(56, 189, 248, 0.3)';
  }
};

const Wishlist = () => {
  return (
    <section id="wishlist" className="relative z-10 py-24 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2
            className="text-4xl md:text-5xl font-bold text-[#F8FAFC] mb-4"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Project Wishlist
          </h2>
          <p
            className="text-lg text-[#94A3B8]"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            Features planned for future releases.
          </p>
        </motion.div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {wishlistItems.map((item, index) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: index * 0.08, ease: 'easeOut' }}
              whileHover={{
                y: -4,
                boxShadow: `0 8px 32px ${getGlowColor(item.status)}`,
                borderColor: getBorderColor(item.status),
              }}
              className="bg-[#0F172A]/50 backdrop-blur-xl border rounded-3xl p-6 cursor-default"
              style={{ borderColor: 'rgba(255,255,255,0.08)', transition: 'box-shadow 0.3s ease, border-color 0.3s ease' }}
            >
              <div className="text-4xl mb-4">{item.icon}</div>
              <h3
                className="text-lg font-semibold text-[#F8FAFC] mb-2"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                {item.title}
              </h3>
              <p
                className="text-sm text-[#94A3B8] mb-4 leading-relaxed"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                {item.description}
              </p>
              <span
                className={`inline-flex px-3 py-1 rounded-full text-xs font-medium border ${getStatusStyles(item.status)}`}
              >
                {item.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Wishlist;
