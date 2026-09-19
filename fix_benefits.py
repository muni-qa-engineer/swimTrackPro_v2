import re

with open('templates/about_swimming.html', 'r') as f:
    content = f.read()

benefits_replacement = """<h3><i class="fa-solid fa-heart-pulse"></i> Health Benefits</h3>
                    <p>Swimming is one of the most complete forms of exercise available, offering benefits across all age groups.</p>
                    <div class="row g-3 mt-3">
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #ef4444; background: rgba(239, 68, 68, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-heart text-danger me-2"></i> Cardio Fitness</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">Strengthens the heart and vastly improves overall blood circulation.</p>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-fire text-warning me-2"></i> Burn Calories</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">Burns anywhere from 400 to over 700 calories per hour based on intensity.</p>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #3b82f6; background: rgba(59, 130, 246, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-dumbbell text-primary me-2"></i> Muscle Toning</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">Water provides 44x more resistance than air, engaging all major muscle groups.</p>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #10b981; background: rgba(16, 185, 129, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-child text-success me-2"></i> Joint-Friendly</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">Buoyancy supports 90% of your body weight, perfect for aging or arthritis.</p>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #8b5cf6; background: rgba(139, 92, 246, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-brain text-purple me-2" style="color: #8b5cf6;"></i> Mental Wellness</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">The rhythmic and sensory experience of swimming reduces stress and anxiety.</p>
                            </div>
                        </div>
                        <div class="col-md-6 col-lg-4">
                            <div class="info-card h-100" style="border-left-color: #06b6d4; background: rgba(6, 182, 212, 0.05); margin-bottom: 0;">
                                <h6 class="fw-bold text-white mb-2"><i class="fa-solid fa-lungs text-info me-2"></i> Lung Capacity</h6>
                                <p class="mb-0 text-muted" style="font-size: 0.85rem;">Regular practice teaches breath control and improves breathing efficiency.</p>
                            </div>
                        </div>
                    </div>"""

content = re.sub(r'<h3><i class="fa-solid fa-heart-pulse"></i> Health Benefits</h3>.*?</ul>', benefits_replacement, content, flags=re.DOTALL)

with open('templates/about_swimming.html', 'w') as f:
    f.write(content)
