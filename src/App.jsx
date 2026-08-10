import Topography from './components/Topography';
import Hero from './components/Hero';
import Wishlist from './components/Wishlist';
import Footer from './components/Footer';

function App() {
  return (
    <div className="relative min-h-screen bg-[#020617]">
      {/* Animated Topography Background */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 0,
          pointerEvents: 'auto',
        }}
      >
        <Topography
          lowColor="#0f172a"
          midColor="#1e293b"
          highColor="#38bdf8"
          speed={0.25}
          morphAmount={2.5}
          morphSpeed={0.04}
          bands={2.0}
          thickness={0.008}
          scale={1.0}
          pixelSize={1.0}
          glow={0.3}
          colorMode="elevation"
          contrast={3.5}
          brightness={0.8}
          fillBands={false}
          opacity={0.6}
          grain={true}
          grainIntensity={0.03}
          mouseInteraction={true}
          mouseRadius={0.25}
          mouseStrength={0.3}
        />
      </div>

      {/* Page Content */}
      <div className="relative z-10">
        <Hero />
        <Wishlist />
        <Footer />
      </div>
    </div>
  );
}

export default App;
