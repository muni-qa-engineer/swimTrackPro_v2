"use client";

import React, { useState } from "react";
import { CoachInfo } from "@/app/actions/booking";
import { BookingStepper } from "./BookingStepper";
import { Step1SessionDetails } from "./Step1SessionDetails";
import { Step2SwimmerDetails } from "./Step2SwimmerDetails";
import { Step3PaymentSummary } from "./Step3PaymentSummary";

interface BookingWizardProps {
  coaches: CoachInfo[];
}

export function BookingWizard({ coaches }: BookingWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);

  // Step 1 States
  const [selectedCoach, setSelectedCoach] = useState<string>(
    coaches.length > 0 ? coaches[0].username : ""
  );
  const [selectedPackage, setSelectedPackage] = useState<string>("monthly_3d");
  const [selectedDays, setSelectedDays] = useState<string[]>([
    "Monday",
    "Wednesday",
    "Friday",
  ]);
  const [startDate, setStartDate] = useState<string>("");
  const [timeSlot, setTimeSlot] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");

  // Step 2 States
  const [swimmerName, setSwimmerName] = useState<string>("");
  const [skillLevel, setSkillLevel] = useState<string>("Beginner");
  const [swimmerCount, setSwimmerCount] = useState<number>(1);
  const [contactPhone, setContactPhone] = useState<string>("");
  const [contactEmail, setContactEmail] = useState<string>("");

  const activeCoach = coaches.find((c) => c.username === selectedCoach);

  return (
    <div className="w-full">
      <BookingStepper currentStep={currentStep} totalSteps={3} />

      {currentStep === 1 && (
        <Step1SessionDetails
          coaches={coaches}
          selectedCoach={selectedCoach}
          setSelectedCoach={setSelectedCoach}
          selectedPackage={selectedPackage}
          setSelectedPackage={setSelectedPackage}
          selectedDays={selectedDays}
          setSelectedDays={setSelectedDays}
          startDate={startDate}
          setStartDate={setStartDate}
          timeSlot={timeSlot}
          setTimeSlot={setTimeSlot}
          location={location}
          setLocation={setLocation}
          latitude={latitude}
          setLatitude={setLatitude}
          longitude={longitude}
          setLongitude={setLongitude}
          onNext={() => setCurrentStep(2)}
        />
      )}

      {currentStep === 2 && (
        <Step2SwimmerDetails
          swimmerName={swimmerName}
          setSwimmerName={setSwimmerName}
          skillLevel={skillLevel}
          setSkillLevel={setSkillLevel}
          swimmerCount={swimmerCount}
          setSwimmerCount={setSwimmerCount}
          contactPhone={contactPhone}
          setContactPhone={setContactPhone}
          contactEmail={contactEmail}
          setContactEmail={setContactEmail}
          selectedPackage={selectedPackage}
          selectedDays={selectedDays}
          onBack={() => setCurrentStep(1)}
          onNext={() => setCurrentStep(3)}
        />
      )}

      {currentStep === 3 && (
        <Step3PaymentSummary
          coach={activeCoach}
          packageKey={selectedPackage}
          startDate={startDate}
          selectedDays={selectedDays}
          timeSlot={timeSlot}
          location={location}
          latitude={latitude}
          longitude={longitude}
          swimmerName={swimmerName}
          skillLevel={skillLevel}
          swimmerCount={swimmerCount}
          contactPhone={contactPhone}
          contactEmail={contactEmail}
          onBack={() => setCurrentStep(2)}
        />
      )}
    </div>
  );
}
