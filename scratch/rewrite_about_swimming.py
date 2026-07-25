import os

html_content = """{% extends 'base.html' %}

{% block title %}About Swimming - SwimTrackPro{% endblock %}

{% block extra_css %}
<style>
    /* Premium Hero Section */
    .hero-section {
        position: relative;
        height: 350px;
        background: url("{{ url_for('static', filename='images/swimming_hero.jpg') }}") no-repeat center center;
        background-attachment: fixed;
        background-size: cover;
        border-radius: var(--radius-lg);
        margin-bottom: 3rem;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    
    .hero-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(6, 182, 212, 0.4) 100%);
        backdrop-filter: blur(4px);
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 4rem;
        animation: fadeInDown 0.8s ease-out;
    }

    .hero-title {
        font-family: var(--font-display);
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 800;
        margin: 0 0 1rem 0;
        background: linear-gradient(to right, #fff, #a5f3fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
    }

    .hero-subtitle {
        font-size: clamp(1rem, 2vw, 1.25rem);
        color: rgba(255,255,255,0.8);
        max-width: 600px;
        line-height: 1.6;
    }
    
    /* Sticky Premium Sidebar */
    .sidebar-sticky {
        position: sticky;
        top: 2rem;
        z-index: 10;
    }
    
    .custom-pills {
        gap: 0.5rem;
        padding-bottom: 1rem;
    }
    
    .custom-pills .nav-link {
        color: var(--color-text-secondary);
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
        font-weight: 600;
        text-align: left;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(10px);
        margin-bottom: 0.25rem;
    }
    
    .custom-pills .nav-link:hover {
        background: rgba(255, 255, 255, 0.05);
        color: white;
        transform: translateX(5px);
        border-color: rgba(255,255,255,0.1);
    }
    
    .custom-pills .nav-link.active {
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.05));
        color: var(--color-primary);
        border-left: 4px solid var(--color-primary);
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.1);
        transform: translateX(5px);
    }
    
    /* Glassmorphism Content Pane */
    .content-pane {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--radius-lg);
        padding: 3rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        animation: fadeUp 0.5s ease-out;
    }
    
    .content-pane h3 {
        color: var(--color-primary);
        font-family: var(--font-display);
        font-size: 2.25rem;
        font-weight: 800;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .content-pane h3 i {
        background: rgba(6, 182, 212, 0.1);
        padding: 12px;
        border-radius: 12px;
        color: var(--color-primary);
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
    }
    
    .content-pane p, .content-pane li {
        font-size: 1.1rem;
        line-height: 1.8;
        color: rgba(255,255,255,0.75);
    }
    
    /* 3D Interactive Cards */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: var(--radius-md);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
        z-index: 1;
    }

    .info-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: var(--color-primary);
        transition: all 0.4s ease;
        z-index: -1;
    }

    .info-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        border-color: rgba(255,255,255,0.1);
        background: rgba(255, 255, 255, 0.05);
    }

    .info-card:hover::before {
        width: 100%;
        opacity: 0.05;
    }
    
    .info-card h5 {
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Premium Imagery */
    .premium-img {
        width: 100%;
        border-radius: var(--radius-lg);
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        max-height: 400px;
        object-fit: cover;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: transform 0.5s ease;
    }

    .premium-img:hover {
        transform: scale(1.02);
    }

    /* Keyframes */
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Responsive */
    @media (max-width: 991.98px) {
        .hero-section { height: 250px; padding: 2rem; background-attachment: scroll; }
        .hero-overlay { padding: 2rem; }
        .content-pane { padding: 1.5rem; }
        .sidebar-sticky { position: static; margin-bottom: 2rem; }
        
        .custom-pills {
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
        .custom-pills .nav-link {
            padding: 0.75rem 1rem;
            margin-bottom: 0;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="container py-5">
    
    <!-- Hero Section -->
    <div class="hero-section">
        <div class="hero-overlay">
            <h1 class="hero-title">The World of Swimming</h1>
            <p class="hero-subtitle">Dive into the comprehensive guide covering everything from basic strokes and health benefits to elite competitive training.</p>
        </div>
    </div>

    <div class="row g-5">
        <!-- Navigation Tabs (Vertical on Desktop, Horizontal Scroll on Mobile) -->
        <div class="col-lg-3">
            <div class="sidebar-sticky">
                <div class="nav flex-column nav-pills custom-pills" id="v-pills-tab" role="tablist" aria-orientation="vertical">
                    <button class="nav-link active" id="pill-intro-tab" data-bs-toggle="pill" data-bs-target="#pill-intro" type="button" role="tab">What is Swimming?</button>
                    <button class="nav-link" id="pill-types-tab" data-bs-toggle="pill" data-bs-target="#pill-types" type="button" role="tab">Types & Strokes</button>
                    <button class="nav-link" id="pill-learn-tab" data-bs-toggle="pill" data-bs-target="#pill-learn" type="button" role="tab">Learning & Drills</button>
                    <button class="nav-link" id="pill-gear-tab" data-bs-toggle="pill" data-bs-target="#pill-gear" type="button" role="tab">Gear & Discipline</button>
                    <button class="nav-link" id="pill-benefits-tab" data-bs-toggle="pill" data-bs-target="#pill-benefits" type="button" role="tab">Health Benefits</button>
                    <button class="nav-link" id="pill-rehab-tab" data-bs-toggle="pill" data-bs-target="#pill-rehab" type="button" role="tab">Rehab & Therapy</button>
                    <button class="nav-link" id="pill-training-tab" data-bs-toggle="pill" data-bs-target="#pill-training" type="button" role="tab">Training & Endurance</button>
                    <button class="nav-link" id="pill-nutrition-tab" data-bs-toggle="pill" data-bs-target="#pill-nutrition" type="button" role="tab">Nutrition</button>
                    <button class="nav-link" id="pill-competition-tab" data-bs-toggle="pill" data-bs-target="#pill-competition" type="button" role="tab">Competitions</button>
                    <button class="nav-link" id="pill-legends-tab" data-bs-toggle="pill" data-bs-target="#pill-legends" type="button" role="tab">Legends</button>
                    <button class="nav-link" id="pill-safety-tab" data-bs-toggle="pill" data-bs-target="#pill-safety" type="button" role="tab">Safety First</button>
                    <button class="nav-link" id="pill-resources-tab" data-bs-toggle="pill" data-bs-target="#pill-resources" type="button" role="tab">Resources</button>
                </div>
            </div>
        </div>

        <!-- Content Area -->
        <div class="col-lg-9">
            <div class="tab-content" id="v-pills-tabContent">
                
                <!-- What is Swimming -->
                <div class="tab-pane fade show active content-pane" id="pill-intro" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-water"></i> What is Swimming?</h3>
                    <p><strong>Swimming</strong> is the self-propulsion of a person through water, usually for recreation, sport, exercise, or survival. Locomotion is achieved through coordinated movement of the limbs and the body to achieve hydrodynamic thrust which results in directional motion.</p>
                    
                    <h5 class="fw-bold text-white mt-5 mb-3" style="font-size: 1.5rem;">Why Swimming?</h5>
                    <p>Unlike many other exercises, swimming is a full-body workout that engages almost every major muscle group while keeping the heart rate up. It is completely low-impact, meaning it takes the stress off your joints, making it sustainable for a lifetime. Whether you want to build strength, lose weight, or find a moving meditation, swimming offers unmatched versatility.</p>
                </div>

                <!-- Types & Strokes -->
                <div class="tab-pane fade content-pane" id="pill-types" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-person-swimming"></i> Types of Swimming</h3>
                    <img src="{{ url_for('static', filename='images/swimming_styles.jpg') }}" alt="Swimming Strokes" class="premium-img">
                    <p class="mb-4">Competitive swimming centers around four primary strokes, each with unique mechanics and benefits. Mastering them requires dedication, technique, and core strength.</p>
                    
                    <div class="row g-4 mt-2">
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #0ea5e9;">
                                <h5 class="text-white"><i class="fa-solid fa-arrow-right" style="color: #0ea5e9;"></i> Freestyle (Front Crawl)</h5>
                                <p class="mb-0 text-muted">The fastest and most efficient stroke. It involves alternating arm movements and a continuous flutter kick.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #10b981;">
                                <h5 class="text-white"><i class="fa-solid fa-frog" style="color: #10b981;"></i> Breaststroke</h5>
                                <p class="mb-0 text-muted">The slowest but most stable stroke. Features a frog-like kick and simultaneous sweeping arm movements.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #a855f7;">
                                <h5 class="text-white"><i class="fa-solid fa-arrow-rotate-left" style="color: #a855f7;"></i> Backstroke</h5>
                                <p class="mb-0 text-muted">Swum on the back, offering easy breathing. It uses alternating arm windmills and a flutter kick.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #ef4444;">
                                <h5 class="text-white"><i class="fa-solid fa-fan" style="color: #ef4444;"></i> Butterfly</h5>
                                <p class="mb-0 text-muted">The most exhausting and difficult stroke. Requires a dolphin kick and simultaneous windmill arms.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Learning & Drills -->
                <div class="tab-pane fade content-pane" id="pill-learn" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-graduation-cap"></i> Learning & Drills</h3>
                    <p>Learning to swim starts with getting comfortable in the water. Beginners focus on <strong>water orientation</strong>—blowing bubbles, floating, and gliding before attempting strokes.</p>
                    
                    <h5 class="fw-bold text-white mt-5 mb-4" style="font-size: 1.5rem;">Essential Drills</h5>
                    <div class="row g-4">
                        <div class="col-12">
                            <div class="info-card p-3">
                                <h6 class="text-white fw-bold mb-2">Kickboard Drills</h6>
                                <p class="mb-0 text-muted small">Isolate the legs for stronger kicks without worrying about arm movements.</p>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="info-card p-3">
                                <h6 class="text-white fw-bold mb-2">Catch-Up Drill</h6>
                                <p class="mb-0 text-muted small">One arm at a time to perfect stroke timing and body rotation.</p>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="info-card p-3">
                                <h6 class="text-white fw-bold mb-2">Fingertip Drag</h6>
                                <p class="mb-0 text-muted small">Trains high-elbow recovery in freestyle, ensuring maximum efficiency.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Gear & Discipline -->
                <div class="tab-pane fade content-pane" id="pill-gear" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-goggles"></i> Gear & Discipline</h3>
                    <p class="mb-4">Having the right equipment is essential for safe and effective swimming. Premium gear enhances hydrodynamics and comfort.</p>
                    <div class="row g-4">
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #06b6d4;">
                                <h5 class="text-white"><i class="fa-solid fa-glasses" style="color: #06b6d4;"></i> Goggles</h5>
                                <p class="mb-0 text-muted">Protect your eyes from chlorine and improve underwater visibility drastically.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #f59e0b;">
                                <h5 class="text-white"><i class="fa-solid fa-hat-cowboy" style="color: #f59e0b;"></i> Swim Cap</h5>
                                <p class="mb-0 text-muted">Reduces drag, protects hair from chemicals, and is mandatory in most pools.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #10b981;">
                                <h5 class="text-white"><i class="fa-solid fa-shirt" style="color: #10b981;"></i> Swimsuit</h5>
                                <p class="mb-0 text-muted">Wear a proper chlorine-resistant swimsuit. Avoid cotton clothing entirely.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #ef4444;">
                                <h5 class="text-white"><i class="fa-solid fa-stopwatch" style="color: #ef4444;"></i> Training Aids</h5>
                                <p class="mb-0 text-muted">Kickboards, pull buoys, and fins isolate muscle groups for targeted improvement.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Health Benefits -->
                <div class="tab-pane fade content-pane" id="pill-benefits" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-heart-pulse"></i> Health Benefits</h3>
                    <p class="mb-4">Swimming is one of the most complete forms of exercise available, offering profound benefits across all age groups.</p>
                    
                    <div class="info-card mb-3" style="--color-primary: #ec4899;">
                        <h6 class="text-white fw-bold"><i class="fa-solid fa-heart me-2 text-pink-500"></i> Cardiovascular Fitness</h6>
                        <p class="mb-0 text-muted small">Strengthens the heart and improves circulation throughout the entire body.</p>
                    </div>
                    <div class="info-card mb-3" style="--color-primary: #eab308;">
                        <h6 class="text-white fw-bold"><i class="fa-solid fa-fire me-2 text-yellow-500"></i> Weight Management</h6>
                        <p class="mb-0 text-muted small">Burns 400-700 calories per hour depending on intensity and stroke.</p>
                    </div>
                    <div class="info-card mb-3" style="--color-primary: #3b82f6;">
                        <h6 class="text-white fw-bold"><i class="fa-solid fa-brain me-2 text-blue-500"></i> Mental Health</h6>
                        <p class="mb-0 text-muted small">The rhythmic nature of swimming reduces stress, anxiety, and depression naturally.</p>
                    </div>
                </div>

                <!-- Rehab & Therapy -->
                <div class="tab-pane fade content-pane" id="pill-rehab" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-hand-holding-medical"></i> Rehab & Therapy</h3>
                    <img src="{{ url_for('static', filename='images/swimming_therapy.jpg') }}" alt="Aquatic Therapy" class="premium-img">
                    <p>Aquatic therapy uses the unique properties of water—buoyancy, resistance, and hydrostatic pressure—for rehabilitation. The buoyancy of water reduces the body's weight by up to 90%, allowing for pain-free movement.</p>
                    
                    <div class="info-card mt-4" style="--color-primary: #14b8a6;">
                        <ul class="mb-0 d-flex flex-column gap-3 text-white list-unstyled">
                            <li><i class="fa-solid fa-check text-teal-500 me-2"></i> <strong>Post-Injury Recovery:</strong> Water supports the body, reducing stress on healing tissues.</li>
                            <li><i class="fa-solid fa-check text-teal-500 me-2"></i> <strong>Arthritis Management:</strong> Warm-water therapy reduces joint stiffness and pain.</li>
                            <li><i class="fa-solid fa-check text-teal-500 me-2"></i> <strong>Back Pain Relief:</strong> Strengthens core muscles that support the spine without axial loading.</li>
                        </ul>
                    </div>
                </div>

                <!-- Training & Endurance -->
                <div class="tab-pane fade content-pane" id="pill-training" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-dumbbell"></i> Training & Endurance</h3>
                    <p>Building swimming endurance requires a structured approach to training, blending aerobic capacity with flawless technique.</p>
                    <ul class="d-flex flex-column gap-3 mt-4 text-white list-unstyled">
                        <li class="p-3 rounded" style="background: rgba(255,255,255,0.05);"><strong class="text-primary d-block mb-1">Interval Training</strong> Instead of swimming continuously, break it down (e.g., 10 x 50m) to maintain technique while building VO2 Max.</li>
                        <li class="p-3 rounded" style="background: rgba(255,255,255,0.05);"><strong class="text-primary d-block mb-1">Pacing</strong> Learning to swim at different "gears" without exhausting yourself in the first 100 meters.</li>
                        <li class="p-3 rounded" style="background: rgba(255,255,255,0.05);"><strong class="text-primary d-block mb-1">Dryland Training</strong> Core exercises, banded pulls, and stretching prevent swimmer's shoulder and improve power transfer.</li>
                    </ul>
                </div>

                <!-- Nutrition -->
                <div class="tab-pane fade content-pane" id="pill-nutrition" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-apple-whole"></i> Nutrition</h3>
                    <p>Swimming demands massive energy. What you eat directly impacts your performance in the water, recovery, and muscle growth.</p>
                    <div class="info-card mt-4" style="--color-primary: #22c55e; background: rgba(34, 197, 94, 0.05);">
                        <ul class="mb-0 d-flex flex-column gap-3 text-white list-unstyled">
                            <li><i class="fa-solid fa-bolt text-success me-2"></i> <strong>Pre-Swim:</strong> Easily digestible carbohydrates 1-2 hours before (bananas, toast, oatmeal).</li>
                            <li><i class="fa-solid fa-droplet text-primary me-2"></i> <strong>Hydration:</strong> Keep a water bottle on the pool deck. Swimming causes sweating too!</li>
                            <li><i class="fa-solid fa-utensils text-warning me-2"></i> <strong>Post-Swim:</strong> A mix of protein and carbs within 45 minutes of finishing to rebuild glycogen.</li>
                        </ul>
                    </div>
                </div>

                <!-- Competitions -->
                <div class="tab-pane fade content-pane" id="pill-competition" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-medal"></i> Competitions & Levels</h3>
                    <p>Competitive swimming tests speed and technique over distances ranging from 50m to 1500m in the pool. Competitions range from local club meets to the pinnacle of international sports.</p>
                    <div class="row g-4 mt-3">
                        <div class="col-12">
                            <div class="info-card p-4" style="--color-primary: #a8a29e;">
                                <h5 class="text-white"><i class="fa-solid fa-users text-stone-400"></i> Club/Local Level</h5>
                                <p class="mb-0 text-muted">Age-group swimming, focusing on personal bests and building racing experience.</p>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="info-card p-4" style="--color-primary: #facc15;">
                                <h5 class="text-white"><i class="fa-solid fa-flag text-yellow-400"></i> National Level</h5>
                                <p class="mb-0 text-muted">Elite domestic competitions such as National Championships and Olympic Trials.</p>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="info-card p-4" style="--color-primary: #3b82f6;">
                                <h5 class="text-white"><i class="fa-solid fa-globe text-blue-500"></i> International Level</h5>
                                <p class="mb-0 text-muted">World Aquatics Championships, Commonwealth Games, and the Olympic Games.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Legends -->
                <div class="tab-pane fade content-pane" id="pill-legends" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-trophy text-warning"></i> Legends of the Pool</h3>
                    <p class="mb-4">The sport has been defined by generational talents who pushed the boundaries of human aquatic potential.</p>
                    
                    <div class="row g-4">
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #eab308; background: linear-gradient(135deg, rgba(234, 179, 8, 0.05), transparent);">
                                <h5 class="fw-bold text-warning mb-4"><i class="fa-solid fa-earth-americas me-2"></i> World Stage</h5>
                                <div class="mb-4">
                                    <strong class="text-white d-block mb-1" style="font-size: 1.1rem;">Michael Phelps (USA)</strong>
                                    <p class="small text-muted mb-0">Most decorated Olympian of all time with 28 medals (23 gold).</p>
                                </div>
                                <div>
                                    <strong class="text-white d-block mb-1" style="font-size: 1.1rem;">Katie Ledecky (USA)</strong>
                                    <p class="small text-muted mb-0">Greatest female distance swimmer in history, dominating the 800m and 1500m freestyle.</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="--color-primary: #f97316; background: linear-gradient(135deg, rgba(249, 115, 22, 0.05), transparent);">
                                <h5 class="fw-bold text-orange-500 mb-4" style="color: #f97316;"><i class="fa-solid fa-flag-in me-2"></i> Indian Icons</h5>
                                <div class="mb-4">
                                    <strong class="text-white d-block mb-1" style="font-size: 1.1rem;">Srihari Nataraj</strong>
                                    <p class="small text-muted mb-0">Elite backstroker who represented India at the Tokyo 2020 Olympics.</p>
                                </div>
                                <div>
                                    <strong class="text-white d-block mb-1" style="font-size: 1.1rem;">Sajan Prakash</strong>
                                    <p class="small text-muted mb-0">Butterfly specialist and the first Indian swimmer to directly qualify for the Olympics.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Safety -->
                <div class="tab-pane fade content-pane" id="pill-safety" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-life-ring"></i> Safety & Precautions</h3>
                    <p class="mb-4">Water is inherently dangerous if proper respect isn't shown. Always prioritize safety over everything else.</p>
                    
                    <div class="info-card" style="--color-primary: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.05);">
                        <ul class="mb-0 d-flex flex-column gap-3 text-white list-unstyled">
                            <li><i class="fa-solid fa-triangle-exclamation text-danger me-3 fs-5"></i> <strong>Never swim alone.</strong> Always swim where a lifeguard is present.</li>
                            <li><i class="fa-solid fa-triangle-exclamation text-danger me-3 fs-5"></i> <strong>Know your limits.</strong> Do not venture into the deep end if you are not a strong swimmer.</li>
                            <li><i class="fa-solid fa-triangle-exclamation text-danger me-3 fs-5"></i> <strong>No running on the deck.</strong> Wet tiles are extremely slippery and cause severe injuries.</li>
                            <li><i class="fa-solid fa-triangle-exclamation text-danger me-3 fs-5"></i> <strong>Shallow Water Blackout:</strong> Never practice prolonged breath-holding underwater without expert supervision.</li>
                        </ul>
                    </div>
                </div>

                <!-- Resources -->
                <div class="tab-pane fade content-pane" id="pill-resources" role="tabpanel" tabindex="0">
                    <h3><i class="fa-solid fa-link"></i> Resources & Links</h3>
                    <p>Explore more about the world of swimming through these authoritative organizations and channels:</p>
                    
                    <div class="row g-3 mt-3">
                        <div class="col-12">
                            <a href="https://www.worldaquatics.com/" target="_blank" class="text-decoration-none">
                                <div class="info-card p-3 d-flex align-items-center gap-3" style="--color-primary: #0ea5e9;">
                                    <div class="bg-primary bg-opacity-10 p-3 rounded-circle text-primary">
                                        <i class="fa-solid fa-globe fs-4"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <h6 class="text-white mb-0 fw-bold">World Aquatics (FINA)</h6>
                                        <small class="text-muted">The international governing body of swimming</small>
                                    </div>
                                    <i class="fa-solid fa-arrow-up-right-from-square text-muted"></i>
                                </div>
                            </a>
                        </div>
                        <div class="col-12">
                            <a href="https://swimming.org.in/" target="_blank" class="text-decoration-none">
                                <div class="info-card p-3 d-flex align-items-center gap-3" style="--color-primary: #f97316;">
                                    <div class="p-3 rounded-circle" style="background: rgba(249, 115, 22, 0.1); color: #f97316;">
                                        <i class="fa-solid fa-flag fs-4"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <h6 class="text-white mb-0 fw-bold">Swimming Federation of India (SFI)</h6>
                                        <small class="text-muted">National governing body in India</small>
                                    </div>
                                    <i class="fa-solid fa-arrow-up-right-from-square text-muted"></i>
                                </div>
                            </a>
                        </div>
                        <div class="col-12">
                            <a href="https://www.youtube.com/c/myswimpro" target="_blank" class="text-decoration-none">
                                <div class="info-card p-3 d-flex align-items-center gap-3" style="--color-primary: #ef4444;">
                                    <div class="p-3 rounded-circle text-danger" style="background: rgba(239, 68, 68, 0.1);">
                                        <i class="fa-brands fa-youtube fs-4"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <h6 class="text-white mb-0 fw-bold">MySwimPro (YouTube)</h6>
                                        <small class="text-muted">Excellent channel for drills, tips, and workouts</small>
                                    </div>
                                    <i class="fa-solid fa-arrow-up-right-from-square text-muted"></i>
                                </div>
                            </a>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</div>

{% set active_page = 'about-swimming' %}
{% include 'components/mobile_bottom_nav.html' %}
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='common.js') }}"></script>
<!-- No custom scrollspy javascript required! Handled entirely by Bootstrap Tabs/Pills -->
{% endblock %}
"""

with open("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/about_swimming.html", "w") as f:
    f.write(html_content)

print("Rewrote about_swimming.html")
