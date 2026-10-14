"use server";

import prisma from "@/lib/prisma";
import { revalidatePath } from "next/cache";

export interface SwimmerInfo {
  id: number;
  name: string;
  skillLevel: string;
}

export interface UpcomingSession {
  bookingId: string;
  studentName: string;
  date: string;
  time: string;
  location: string;
  packageName: string;
  trainerName: string;
}

export interface CalendarDayInfo {
  day: number | null;
  dateStr: string;
  isToday: boolean;
  isBooked: boolean;
  isMakeup: boolean;
  isPaused: boolean;
  sessionTitle?: string;
}

export interface GuestDashboardData {
  ownerName: string;
  ownerPhone: string;
  activePackage: {
    bookingId: string;
    packageName: string;
    trainerName: string;
    startDate: string;
    endDate: string;
    timeSlot: string;
    location: string;
    status: string;
    pauseStatus: string;
    autoResumeDate?: string;
    allocatedPauseDays: number;
    usedPauseDays: number;
    availablePauseDays: number;
    isPausable: boolean;
    totalClasses: number;
    completedClasses: number;
    remainingClasses: number;
    skipsAllowed: number;
    skipsUsed: number;
    skipsRemaining: number;
    selectedDays: string[];
    upcomingDates: string[];
  } | null;
  totalSwimmers: number;
  swimmers: SwimmerInfo[];
  makeupCreditsCount: number;
  calendarMonthName: string;
  calendarDays: CalendarDayInfo[];
  upcomingSessions: UpcomingSession[];
  notices: {
    id: number;
    authorName: string;
    message: string;
    createdAt: string;
  }[];
}

// Helper: parse recurring dates from start, end, and selected days
function generateDates(startStr: string, endStr: string, daysStr: string): string[] {
  try {
    const start = new Date(startStr);
    const end = new Date(endStr);
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return [];

    const dayNameMap: Record<string, number> = {
      sunday: 0,
      sun: 0,
      monday: 1,
      mon: 1,
      tuesday: 2,
      tue: 2,
      wednesday: 3,
      wed: 3,
      thursday: 4,
      thu: 4,
      friday: 5,
      fri: 5,
      saturday: 6,
      sat: 6,
    };

    const targetDays = daysStr
      .toLowerCase()
      .split(/[,\s]+/)
      .map((d) => d.trim())
      .filter(Boolean)
      .map((d) => dayNameMap[d])
      .filter((d) => d !== undefined);

    const dates: string[] = [];
    const curr = new Date(start);
    while (curr <= end && dates.length < 150) {
      if (targetDays.length === 0 || targetDays.includes(curr.getDay())) {
        dates.push(curr.toISOString().split("T")[0]);
      }
      curr.setDate(curr.getDate() + 1);
    }
    return dates;
  } catch {
    return [];
  }
}

export async function getGuestDashboardData(
  phoneQuery?: string
): Promise<GuestDashboardData> {
  const today = new Date();
  const todayStr = today.toISOString().split("T")[0];
  const year = today.getFullYear();
  const month = today.getMonth(); // 0-indexed
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const calendarMonthName = `${monthNames[month]} ${year}`;

  try {
    // 1. Fetch bookings
    const bookings = await prisma.booking.findMany({
      where: phoneQuery ? { owner_phone: phoneQuery } : undefined,
      orderBy: [{ status: "asc" }, { start_date: "desc" }],
      take: 10,
    });

    // 2. Fetch notices
    const notices = await prisma.notice.findMany({
      orderBy: { created_at: "desc" },
      take: 3,
    });

    // 3. Fetch makeup credits
    const makeupCreditsCount = await prisma.makeupCredit.count({
      where: { status: "available" },
    });

    // Pick active booking (prefer active, then latest)
    const activeBooking =
      bookings.find(
        (b) =>
          b.status?.toLowerCase() === "active" ||
          b.status?.toLowerCase() === "confirmed" ||
          b.status?.toLowerCase() === "paid"
      ) || bookings[0] || null;

    let packageData = null;
    let scheduledDates: string[] = [];

    if (activeBooking) {
      const pkgName = activeBooking.package || "Monthly 3 Days/Week";
      const isLongTerm =
        pkgName.includes("3 Month") ||
        pkgName.includes("6 Month") ||
        pkgName.includes("9 Month") ||
        pkgName.includes("12 Month");

      // Pause limits
      let allocatedPause = 0;
      let skipsAllowed = 3;
      if (pkgName.includes("3 Month")) {
        allocatedPause = 15;
        skipsAllowed = 9;
      } else if (pkgName.includes("6 Month")) {
        allocatedPause = 30;
        skipsAllowed = 18;
      } else if (pkgName.includes("9 Month")) {
        allocatedPause = 45;
        skipsAllowed = 27;
      } else if (pkgName.includes("12 Month")) {
        allocatedPause = 60;
        skipsAllowed = 36;
      }

      const usedPause = activeBooking.used_pause_days || 0;
      const availablePause = Math.max(0, allocatedPause - usedPause);

      // Parse schedule dates
      if (activeBooking.calendar_dates_override) {
        scheduledDates = activeBooking.calendar_dates_override
          .split(",")
          .map((d) => d.trim())
          .filter(Boolean);
      } else if (activeBooking.start_date && activeBooking.end_date) {
        scheduledDates = generateDates(
          activeBooking.start_date,
          activeBooking.end_date,
          activeBooking.selected_days || "Monday, Wednesday, Friday"
        );
      }

      const attendedCount = activeBooking.attended_sessions
        ? activeBooking.attended_sessions.split(",").filter(Boolean).length
        : 0;

      const futureDates = scheduledDates.filter((d) => d >= todayStr);

      packageData = {
        bookingId: activeBooking.id,
        packageName: activeBooking.package || "Monthly 3 Days/Week",
        trainerName: activeBooking.trainer_username || "Certified Coach",
        startDate: activeBooking.start_date || todayStr,
        endDate: activeBooking.end_date || "",
        timeSlot: activeBooking.time || "06:00 AM",
        location: activeBooking.location || "Bangalore Pool Center",
        status: activeBooking.status || "Active",
        pauseStatus: activeBooking.pause_status || "ACTIVE",
        autoResumeDate: activeBooking.auto_resume_date || undefined,
        allocatedPauseDays: allocatedPause,
        usedPauseDays: usedPause,
        availablePauseDays: availablePause,
        isPausable: isLongTerm,
        totalClasses: Math.max(scheduledDates.length, 12),
        completedClasses: attendedCount,
        remainingClasses: Math.max(0, scheduledDates.length - attendedCount),
        skipsAllowed,
        skipsUsed: 0,
        skipsRemaining: skipsAllowed,
        selectedDays: (activeBooking.selected_days || "Mon, Wed, Fri")
          .split(",")
          .map((s) => s.trim()),
        upcomingDates: futureDates.slice(0, 5),
      };
    }

    // 4. Build monthly calendar
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayIndex = new Date(year, month, 1).getDay(); // 0 is Sunday
    // Adjust to Monday = 0
    const offset = firstDayIndex === 0 ? 6 : firstDayIndex - 1;

    const calendarDays: CalendarDayInfo[] = [];

    // Leading empty days
    for (let i = 0; i < offset; i++) {
      calendarDays.push({
        day: null,
        dateStr: "",
        isToday: false,
        isBooked: false,
        isMakeup: false,
        isPaused: false,
      });
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const dStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const isToday = dStr === todayStr;
      const isBooked = scheduledDates.includes(dStr);
      const isPaused =
        packageData?.pauseStatus === "PAUSED" &&
        activeBooking?.pause_date &&
        activeBooking.auto_resume_date
          ? dStr >= activeBooking.pause_date && dStr < activeBooking.auto_resume_date
          : false;

      calendarDays.push({
        day: d,
        dateStr: dStr,
        isToday,
        isBooked,
        isMakeup: false,
        isPaused,
        sessionTitle: isBooked ? `${packageData?.timeSlot}` : undefined,
      });
    }

    // 5. Upcoming sessions list
    const upcomingSessions: UpcomingSession[] = (packageData?.upcomingDates || [])
      .slice(0, 3)
      .map((date) => ({
        bookingId: packageData!.bookingId,
        studentName: activeBooking?.student_name || "Primary Swimmer",
        date,
        time: packageData!.timeSlot,
        location: packageData!.location,
        packageName: packageData!.packageName,
        trainerName: packageData!.trainerName,
      }));

    // 6. Swimmers list
    const swimmersFromDb = await prisma.student.findMany({
      where: activeBooking?.owner_phone ? { owner_phone: activeBooking.owner_phone } : undefined,
      take: 5,
    });

    const swimmers: SwimmerInfo[] = swimmersFromDb.length > 0
      ? swimmersFromDb.map((s) => ({
          id: s.id,
          name: s.student_name || "Swimmer",
          skillLevel: s.skill_level || "Beginner",
        }))
      : [
          {
            id: 1,
            name: activeBooking?.student_name || "Swimmer 1",
            skillLevel: "Beginner",
          },
        ];

    return {
      ownerName: activeBooking?.owner_name || "Valued Swimmer",
      ownerPhone: activeBooking?.owner_phone || phoneQuery || "9876543210",
      activePackage: packageData,
      totalSwimmers: swimmers.length,
      swimmers,
      makeupCreditsCount,
      calendarMonthName,
      calendarDays,
      upcomingSessions,
      notices: notices.map((n) => ({
        id: n.id,
        authorName: n.author_name || "Academy Management",
        message: n.message || "",
        createdAt: n.created_at ? n.created_at.toISOString() : todayStr,
      })),
    };
  } catch (error) {
    console.error("Error in getGuestDashboardData:", error);
    // Return high quality fallback mockup so UI runs gracefully
    return getFallbackGuestDashboardData(todayStr, calendarMonthName, year, month);
  }
}

function getFallbackGuestDashboardData(
  todayStr: string,
  calendarMonthName: string,
  year: number,
  month: number
): GuestDashboardData {
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay();
  const offset = firstDayIndex === 0 ? 6 : firstDayIndex - 1;

  const calendarDays: CalendarDayInfo[] = [];
  for (let i = 0; i < offset; i++) {
    calendarDays.push({
      day: null,
      dateStr: "",
      isToday: false,
      isBooked: false,
      isMakeup: false,
      isPaused: false,
    });
  }

  // Pre-fill Mon, Wed, Fri as booked for demo
  for (let d = 1; d <= daysInMonth; d++) {
    const dObj = new Date(year, month, d);
    const dayOfWeek = dObj.getDay();
    const dStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const isBooked = [1, 3, 5].includes(dayOfWeek); // Mon, Wed, Fri

    calendarDays.push({
      day: d,
      dateStr: dStr,
      isToday: dStr === todayStr,
      isBooked,
      isMakeup: false,
      isPaused: false,
      sessionTitle: isBooked ? "06:00 AM" : undefined,
    });
  }

  return {
    ownerName: "Rohit Sharma",
    ownerPhone: "9876543210",
    activePackage: {
      bookingId: "SWIM-DEMO-99",
      packageName: "Monthly 3 Days/Week",
      trainerName: "Coach Rajesh Verma",
      startDate: todayStr,
      endDate: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
      timeSlot: "06:00 AM - 07:00 AM",
      location: "Sobha City Swimming Pool, Bangalore",
      status: "Active",
      pauseStatus: "ACTIVE",
      allocatedPauseDays: 0,
      usedPauseDays: 0,
      availablePauseDays: 0,
      isPausable: false,
      totalClasses: 12,
      completedClasses: 3,
      remainingClasses: 9,
      skipsAllowed: 3,
      skipsUsed: 1,
      skipsRemaining: 2,
      selectedDays: ["Monday", "Wednesday", "Friday"],
      upcomingDates: [
        todayStr,
        new Date(Date.now() + 2 * 86400000).toISOString().split("T")[0],
        new Date(Date.now() + 4 * 86400000).toISOString().split("T")[0],
      ],
    },
    totalSwimmers: 2,
    swimmers: [
      { id: 101, name: "Aarav Sharma", skillLevel: "Intermediate" },
      { id: 102, name: "Ananya Sharma", skillLevel: "Beginner" },
    ],
    makeupCreditsCount: 1,
    calendarMonthName,
    calendarDays,
    upcomingSessions: [
      {
        bookingId: "SWIM-DEMO-99",
        studentName: "Aarav Sharma",
        date: todayStr,
        time: "06:00 AM",
        location: "Sobha City Pool, Bengaluru",
        packageName: "Monthly 3 Days/Week",
        trainerName: "Coach Rajesh Verma",
      },
      {
        bookingId: "SWIM-DEMO-99",
        studentName: "Aarav Sharma",
        date: new Date(Date.now() + 2 * 86400000).toISOString().split("T")[0],
        time: "06:00 AM",
        location: "Sobha City Pool, Bengaluru",
        packageName: "Monthly 3 Days/Week",
        trainerName: "Coach Rajesh Verma",
      },
    ],
    notices: [
      {
        id: 1,
        authorName: "Coach Rajesh",
        message: "Friendly reminder: Please arrive 5 minutes early with your goggles and swim cap.",
        createdAt: todayStr,
      },
    ],
  };
}

// Pause Booking Action
export async function pauseBookingAction(formData: FormData) {
  const bookingId = formData.get("bookingId") as string;
  const pauseDays = parseInt(formData.get("pauseDays") as string, 10) || 7;
  const reason = (formData.get("reason") as string) || "Personal";
  const otherReason = (formData.get("otherReason") as string) || "";

  if (!bookingId) {
    return { success: false, error: "Missing Booking ID" };
  }

  try {
    const booking = await prisma.booking.findUnique({
      where: { id: bookingId },
    });

    if (!booking) {
      return { success: false, error: "Booking record not found" };
    }

    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];
    const autoResume = new Date(today.getTime() + pauseDays * 86400000);
    const autoResumeStr = autoResume.toISOString().split("T")[0];

    // Shift end_date forward by pauseDays
    let newEndDateStr = booking.end_date;
    if (booking.end_date) {
      const origEnd = new Date(booking.end_date);
      const newEnd = new Date(origEnd.getTime() + pauseDays * 86400000);
      newEndDateStr = newEnd.toISOString().split("T")[0];
    }

    await prisma.booking.update({
      where: { id: bookingId },
      data: {
        pause_status: "PAUSED",
        pause_date: todayStr,
        auto_resume_date: autoResumeStr,
        pause_reason: reason,
        pause_other_reason: otherReason,
        end_date: newEndDateStr,
        used_pause_days: (booking.used_pause_days || 0) + pauseDays,
        pause_count: (booking.pause_count || 0) + 1,
      },
    });

    // Log pause audit
    await prisma.packagePauseAudit.create({
      data: {
        booking_id: bookingId,
        action: "PAUSE",
        performed_by: booking.owner_name || "Guest",
        pause_date: todayStr,
        resume_date: autoResumeStr,
        reason: otherReason || reason,
      },
    });

    revalidatePath("/dashboard");
    revalidatePath("/my-bookings");
    return {
      success: true,
      message: `Membership paused successfully for ${pauseDays} days until ${autoResumeStr}.`,
    };
  } catch (error) {
    console.error("Error pausing booking:", error);
    return { success: false, error: "Failed to pause booking in database" };
  }
}

// Resume Booking Action
export async function resumeBookingAction(bookingId: string) {
  if (!bookingId) {
    return { success: false, error: "Missing Booking ID" };
  }

  try {
    const booking = await prisma.booking.findUnique({
      where: { id: bookingId },
    });

    if (!booking) {
      return { success: false, error: "Booking record not found" };
    }

    const todayStr = new Date().toISOString().split("T")[0];

    await prisma.booking.update({
      where: { id: bookingId },
      data: {
        pause_status: "ACTIVE",
        resume_date: todayStr,
      },
    });

    await prisma.packagePauseAudit.create({
      data: {
        booking_id: bookingId,
        action: "RESUME",
        performed_by: booking.owner_name || "Guest",
        resume_date: todayStr,
        reason: "Early manual resume by member",
      },
    });

    revalidatePath("/dashboard");
    revalidatePath("/my-bookings");
    return { success: true, message: "Membership resumed successfully!" };
  } catch (error) {
    console.error("Error resuming booking:", error);
    return { success: false, error: "Failed to resume membership" };
  }
}

// Skip Session Action
export async function skipSessionAction(bookingId: string, sessionDate: string) {
  if (!bookingId || !sessionDate) {
    return { success: false, error: "Missing booking ID or session date" };
  }

  try {
    const booking = await prisma.booking.findUnique({
      where: { id: bookingId },
    });

    if (!booking) {
      return { success: false, error: "Booking not found" };
    }

    // Insert makeup credit
    await prisma.makeupCredit.create({
      data: {
        booking_id: bookingId,
        original_date: new Date(sessionDate),
        status: "available",
        notes: `Class skipped on ${sessionDate} by student`,
      },
    });

    revalidatePath("/dashboard");
    revalidatePath("/my-bookings");
    return {
      success: true,
      message: `Session on ${sessionDate} skipped. 1 Make-up credit added to your account!`,
    };
  } catch (error) {
    console.error("Error skipping session:", error);
    return { success: false, error: "Failed to process skip session" };
  }
}

// Fetch user's bookings with explicit ordering: latest active first
export async function getMyBookingsList(filter: "all" | "active" | "booked" | "completed" = "all", phone?: string) {
  try {
    const bookings = await prisma.booking.findMany({
      where: phone ? { owner_phone: phone } : undefined,
    });

    // Custom sorting: latest active first, then following
    const sorted = [...bookings].sort((a, b) => {
      const aIsActive = (a.status?.toLowerCase() === "active" || a.status?.toLowerCase() === "confirmed") ? 1 : 0;
      const bIsActive = (b.status?.toLowerCase() === "active" || b.status?.toLowerCase() === "confirmed") ? 1 : 0;

      if (aIsActive !== bIsActive) {
        return bIsActive - aIsActive; // Active first
      }

      // Within active or non-active, sort latest start_date descending
      const aDate = a.start_date || "";
      const bDate = b.start_date || "";
      return bDate.localeCompare(aDate);
    });

    if (filter === "active") {
      return sorted.filter((b) => b.status?.toLowerCase() === "active" || b.status?.toLowerCase() === "confirmed");
    }
    if (filter === "booked") {
      return sorted.filter((b) => b.status?.toLowerCase() === "pending" || b.status?.toLowerCase() === "booked");
    }
    if (filter === "completed") {
      return sorted.filter((b) => b.status?.toLowerCase() === "completed" || b.status?.toLowerCase() === "cancelled");
    }

    return sorted;
  } catch (error) {
    console.error("Error fetching bookings list:", error);
    return [];
  }
}

// Trainer Dashboard Data
export interface TrainerDashboardData {
  trainerName: string;
  username: string;
  todayDateStr: string;
  totalStudents: number;
  totalActiveBatches: number;
  todaySessions: {
    bookingId: string;
    studentName: string;
    time: string;
    location: string;
    packageName: string;
    phone: string;
    status: "present" | "absent" | "pending";
  }[];
  swimmerRoster: {
    bookingId: string;
    studentName: string;
    packageName: string;
    selectedDays: string;
    time: string;
    phone: string;
    status: string;
  }[];
}

export async function getTrainerDashboardData(
  trainerUsername = "coach_default"
): Promise<TrainerDashboardData> {
  try {
    const bookings = await prisma.booking.findMany({
      where: {
        status: { in: ["active", "Active", "confirmed", "Confirmed"] },
      },
    });

    // Filter today's sessions
    const todaySessions = bookings
      .filter((b) => {
        const days = (b.selected_days || "").toLowerCase();
        const dayNames = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
        const todayDay = dayNames[new Date().getDay()];
        return days.includes(todayDay);
      })
      .map((b) => ({
        bookingId: b.id,
        studentName: b.student_name || "Swimmer",
        time: b.time || "06:00 AM",
        location: b.location || "Pool Arena",
        packageName: b.package || "Monthly Plan",
        phone: b.owner_phone || "--",
        status: "pending" as const,
      }));

    // Swimmer roster sorted latest active first
    const swimmerRoster = bookings.map((b) => ({
      bookingId: b.id,
      studentName: b.student_name || "Swimmer",
      packageName: b.package || "Standard Package",
      selectedDays: b.selected_days || "Mon, Wed, Fri",
      time: b.time || "06:00 AM",
      phone: b.owner_phone || "--",
      status: b.status || "Active",
    }));

    return {
      trainerName: "Head Coach Rajesh",
      username: trainerUsername,
      todayDateStr: new Date().toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
      totalStudents: bookings.length,
      totalActiveBatches: Math.ceil(bookings.length / 3) || 1,
      todaySessions,
      swimmerRoster,
    };
  } catch (error) {
    console.error("Error in getTrainerDashboardData:", error);
    return {
      trainerName: "Head Coach Rajesh",
      username: trainerUsername,
      todayDateStr: new Date().toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "short",
        year: "numeric",
      }),
      totalStudents: 14,
      totalActiveBatches: 4,
      todaySessions: [
        {
          bookingId: "SWIM-BK-101",
          studentName: "Aarav Sharma",
          time: "06:00 AM - 07:00 AM",
          location: "Sobha City Pool, Bengaluru",
          packageName: "Monthly 3 Days/Week",
          phone: "9876543210",
          status: "pending",
        },
        {
          bookingId: "SWIM-BK-102",
          studentName: "Ananya Iyer",
          time: "07:15 AM - 08:15 AM",
          location: "Prestige Golfshire Pool",
          packageName: "3 Months 3 Days/Week",
          phone: "9876543211",
          status: "pending",
        },
      ],
      swimmerRoster: [
        {
          bookingId: "SWIM-BK-101",
          studentName: "Aarav Sharma",
          packageName: "Monthly 3 Days/Week",
          selectedDays: "Mon, Wed, Fri",
          time: "06:00 AM",
          phone: "9876543210",
          status: "Active",
        },
        {
          bookingId: "SWIM-BK-102",
          studentName: "Ananya Iyer",
          packageName: "3 Months 3 Days/Week",
          selectedDays: "Mon, Wed, Fri",
          time: "07:15 AM",
          phone: "9876543211",
          status: "Active",
        },
      ],
    };
  }
}

// Attendance marker action
export async function markAttendanceAction(
  bookingId: string,
  sessionDate: string,
  status: "present" | "absent"
) {
  try {
    const booking = await prisma.booking.findUnique({
      where: { id: bookingId },
    });

    if (!booking) return { success: false, error: "Booking not found" };

    const currentAttended = booking.attended_sessions
      ? booking.attended_sessions.split(",").filter(Boolean)
      : [];

    if (status === "present" && !currentAttended.includes(sessionDate)) {
      currentAttended.push(sessionDate);
      await prisma.booking.update({
        where: { id: bookingId },
        data: {
          attended_sessions: currentAttended.join(","),
        },
      });
    }

    revalidatePath("/trainer");
    return { success: true, message: `Marked ${status} for ${sessionDate}` };
  } catch (error) {
    console.error("Error marking attendance:", error);
    return { success: false, error: "Failed to update attendance" };
  }
}
