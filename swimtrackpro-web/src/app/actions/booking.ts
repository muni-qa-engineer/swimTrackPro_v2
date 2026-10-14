"use server";

import { prisma } from "@/lib/prisma";
import { getPackageQuote } from "@/lib/pricingEngine";
import { revalidatePath } from "next/cache";

export interface CoachInfo {
  username: string;
  name: string;
  phone: string | null;
  experience: string | null;
  qualification: string | null;
  residenceLocation: string | null;
  rating: number;
  availableSlots: string[];
  notice: string | null;
}

export async function getActiveCoaches(): Promise<CoachInfo[]> {
  try {
    const trainers = await prisma.trainer.findMany({
      where: {
        is_blocked: false,
      },
      select: {
        username: true,
        name: true,
        phone: true,
        experience: true,
        qualification: true,
        residence_location: true,
        rating: true,
        available_slots: true,
        notice: true,
      },
      orderBy: {
        name: "asc",
      },
    });

    return trainers.map((t) => {
      let slots: string[] = [];
      try {
        if (t.available_slots) {
          slots = JSON.parse(t.available_slots);
        }
      } catch {
        slots = [];
      }

      return {
        username: t.username,
        name: t.name,
        phone: t.phone,
        experience: t.experience || "Certified Coach",
        qualification: t.qualification || "Swimming Instructor",
        residenceLocation: t.residence_location || "Hyderabad",
        rating: t.rating ? Number(t.rating) : 5.0,
        availableSlots: Array.isArray(slots) ? slots : [],
        notice: t.notice,
      };
    });
  } catch (error) {
    console.error("Failed to load active coaches:", error);
    return [];
  }
}

export async function checkSlotConflict(params: {
  trainerUsername: string;
  date: string;
  time: string;
  location: string;
}): Promise<{ conflict: boolean; message?: string }> {
  try {
    const { trainerUsername, date, time, location } = params;
    if (!trainerUsername || !date || !time) {
      return { conflict: false };
    }

    const cleanDate = date.trim();
    const cleanTime = time.trim().toLowerCase();
    const cleanLoc = (location || "").trim().toLowerCase();

    // Check existing non-cancelled bookings for this trainer
    const existingBookings = await prisma.booking.findMany({
      where: {
        trainer_username: trainerUsername,
        time: {
          contains: cleanTime,
          mode: "insensitive",
        },
        NOT: {
          status: { in: ["cancelled", "deleted", "completed"] },
        },
      },
      select: {
        id: true,
        start_date: true,
        end_date: true,
        selected_days: true,
        location: true,
        time: true,
      },
    });

    for (const b of existingBookings) {
      const bLoc = (b.location || "").trim().toLowerCase();
      // If booked at a different location on overlapping dates
      if (bLoc && cleanLoc && bLoc !== cleanLoc) {
        if (b.start_date && b.end_date) {
          if (cleanDate >= b.start_date && cleanDate <= b.end_date) {
            return {
              conflict: true,
              message: `Coach is already scheduled at another pool (${b.location}) during this time slot.`,
            };
          }
        } else if (b.start_date === cleanDate) {
          return {
            conflict: true,
            message: `Coach is already scheduled at another pool (${b.location}) on this day.`,
          };
        }
      }
    }

    return { conflict: false };
  } catch (error) {
    console.error("Error checking slot conflict:", error);
    return { conflict: false };
  }
}

export interface BookingSubmissionInput {
  trainerUsername: string;
  packageKey: string;
  startDate: string;
  endDate?: string;
  selectedDays: string[];
  time: string;
  location: string;
  latitude?: string;
  longitude?: string;
  swimmerName: string;
  skillLevel: string;
  swimmerCount: number;
  contactPhone: string;
  contactEmail?: string;
  ownerName?: string;
}

export async function createBooking(input: BookingSubmissionInput): Promise<{
  success: boolean;
  bookingId?: string;
  bookingCode?: string;
  totalFee?: number;
  error?: string;
}> {
  try {
    // 1. Validations
    if (!input.swimmerName.trim()) {
      return { success: false, error: "Swimmer name is required." };
    }
    const cleanPhone = input.contactPhone.replace(/\D/g, "");
    if (cleanPhone.length !== 10) {
      return { success: false, error: "Please enter a valid 10-digit mobile number." };
    }
    if (!input.location.trim()) {
      return { success: false, error: "Pool location is required." };
    }
    if (!input.trainerUsername) {
      return { success: false, error: "Please select an assigned coach." };
    }
    if (!input.startDate) {
      return { success: false, error: "Please select a training start date." };
    }

    const swimmerCount = Math.min(5, Math.max(1, input.swimmerCount || 1));
    const weeklyDaysCount = input.selectedDays.length;

    // Package day restrictions
    const pkg = input.packageKey.toLowerCase();
    if (pkg.includes("monthly") && (weeklyDaysCount < 2 || weeklyDaysCount > 3)) {
      return { success: false, error: "Monthly pack requires selecting 2 or 3 training days per week." };
    }
    if (["3_months", "6_months", "9_months", "12_months"].includes(pkg) && weeklyDaysCount !== 3) {
      return { success: false, error: "Long term packages require selecting exactly 3 training days per week." };
    }

    // 2. Fee Calculation
    const quote = getPackageQuote(input.packageKey, swimmerCount, {
      weeklyDays: weeklyDaysCount,
    });
    const totalFee = quote.totalBatchPrice;

    // 3. ID and Booking Code Generation
    const timestamp = Date.now().toString().slice(-6);
    const randomHex = Math.random().toString(36).substring(2, 6).toUpperCase();
    const bookingId = `BK-${Date.now()}`;
    const bookingCode = `STP${timestamp}${randomHex}`;

    // 4. Calculate End Date if not provided (4 weeks for monthly, 12 wks for 3m, etc.)
    let calculatedEndDate = input.endDate || "";
    if (!calculatedEndDate && input.startDate) {
      const start = new Date(input.startDate);
      let daysToAdd = 28; // Default 4 weeks
      if (pkg === "single" || pkg === "demo") daysToAdd = 0;
      else if (pkg === "3_months") daysToAdd = 90;
      else if (pkg === "6_months") daysToAdd = 180;
      else if (pkg === "9_months") daysToAdd = 270;
      else if (pkg === "12_months") daysToAdd = 365;

      start.setDate(start.getDate() + daysToAdd);
      calculatedEndDate = start.toISOString().split("T")[0];
    }

    const owner = input.ownerName || input.swimmerName;

    // 5. Insert Booking into PostgreSQL
    await prisma.booking.create({
      data: {
        id: bookingId,
        booking_code: bookingCode,
        student_name: input.swimmerName.trim(),
        created_by: owner.trim(),
        owner_name: owner.trim(),
        owner_phone: cleanPhone,
        email: (input.contactEmail || "").trim(),
        start_date: input.startDate,
        end_date: calculatedEndDate,
        package: quote.packageName,
        selected_days: input.selectedDays.join(", "),
        location: input.location.trim(),
        latitude: input.latitude || null,
        longitude: input.longitude || null,
        persons: swimmerCount,
        time: input.time,
        fee: totalFee,
        status: "unconfirmed",
        payment_request: "unconfirmed",
        trainer_username: input.trainerUsername,
        package_status: "ACTIVE",
        pause_status: "ACTIVE",
        allocated_pause_days: quote.pauseDays,
        used_pause_days: 0,
      },
    });

    // 6. Upsert Student profile
    await prisma.student.create({
      data: {
        student_name: input.swimmerName.trim(),
        owner_name: owner.trim(),
        owner_phone: cleanPhone,
        skill_level: input.skillLevel || "Beginner",
        is_blocked: false,
      },
    });

    revalidatePath("/booking");
    revalidatePath("/my-bookings");
    revalidatePath("/");

    return {
      success: true,
      bookingId,
      bookingCode,
      totalFee,
    };
  } catch (error) {
    console.error("Booking submission failed:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to create booking. Please try again.",
    };
  }
}
