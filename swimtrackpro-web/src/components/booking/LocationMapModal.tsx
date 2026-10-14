"use client";

import React, { useState } from "react";
import { MapPin, Navigation, X, Check, Loader2 } from "lucide-react";

interface LocationMapModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectLocation: (address: string, lat?: string, lng?: string) => void;
  initialLocation?: string;
}

export function LocationMapModal({
  isOpen,
  onClose,
  onSelectLocation,
}: LocationMapModalProps) {
  const [detecting, setDetecting] = useState(false);
  const [detectedAddress, setDetectedAddress] = useState("");
  const [coords, setCoords] = useState<{ lat: string; lng: string } | null>(null);

  if (!isOpen) return null;

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    setDetecting(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude.toFixed(6);
          const lng = pos.coords.longitude.toFixed(6);
          setCoords({ lat, lng });

          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`
          );
          const data = await res.json();
          const address = data.display_name || `${lat}, ${lng}`;
          setDetectedAddress(address);
        } catch {
          const fallback = `${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`;
          setDetectedAddress(fallback);
        } finally {
          setDetecting(false);
        }
      },
      () => {
        alert("Unable to fetch current GPS coordinates. Please enter pool address manually.");
        setDetecting(false);
      }
    );
  };

  const handleConfirm = () => {
    if (detectedAddress) {
      onSelectLocation(detectedAddress, coords?.lat, coords?.lng);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-xl">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Choose Pool Location</h3>
            <p className="text-xs text-slate-400">Select doorstep pool via GPS or map coordinates</p>
          </div>
        </div>

        <div className="space-y-4">
          <button
            type="button"
            onClick={handleUseCurrentLocation}
            disabled={detecting}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl transition shadow-lg shadow-cyan-500/20 disabled:opacity-50"
          >
            {detecting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Acquiring GPS Signal...</span>
              </>
            ) : (
              <>
                <Navigation className="w-5 h-5" />
                <span>Use Current Location</span>
              </>
            )}
          </button>

          {detectedAddress && (
            <div className="p-4 bg-slate-950/60 border border-cyan-500/30 rounded-xl text-left">
              <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                Detected Address
              </span>
              <p className="text-sm text-slate-200 line-clamp-3">{detectedAddress}</p>
              {coords && (
                <p className="text-[11px] text-slate-400 mt-2 font-mono">
                  Coordinates: {coords.lat}, {coords.lng}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-sm font-semibold transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!detectedAddress}
            className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-sm font-bold transition flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Check className="w-4 h-4" />
            <span>Apply Location</span>
          </button>
        </div>
      </div>
    </div>
  );
}
