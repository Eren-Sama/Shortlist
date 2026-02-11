"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/components/auth-provider";
import { createClient } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  User,
  MapPin,
  Github,
  Linkedin,
  Save,
  Check,
  Briefcase,
  Plus,
  X,
  Camera,
  Upload,
} from "lucide-react";

interface ProfileData {
  full_name: string;
  bio: string;
  location: string;
  skills: string[];
  github_url: string;
  linkedin_url: string;
  title: string;
  avatar_url: string;
}

const emptyProfile: ProfileData = {
  full_name: "",
  bio: "",
  location: "",
  skills: [],
  github_url: "",
  linkedin_url: "",
  title: "",
  avatar_url: "",
};

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileData>(emptyProfile);
  const [newSkill, setNewSkill] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user?.user_metadata) {
      const m = user.user_metadata;
      setProfile({
        full_name: m.full_name || "",
        bio: m.bio || "",
        location: m.location || "",
        skills: m.skills || [],
        github_url: m.github_url || "",
        linkedin_url: m.linkedin_url || "",
        title: m.title || "",
        avatar_url: m.avatar_url || "",
      });
    }
  }, [user]);

  const handleChange = useCallback(
    (field: keyof ProfileData, value: string) => {
      setProfile((p) => ({ ...p, [field]: value }));
      setSaved(false);
    },
    []
  );

  const addSkill = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !profile.skills.includes(trimmed)) {
      setProfile((p) => ({ ...p, skills: [...p.skills, trimmed] }));
      setNewSkill("");
      setSaved(false);
    }
  };

  const removeSkill = (skill: string) => {
    setProfile((p) => ({
      ...p,
      skills: p.skills.filter((s) => s !== skill),
    }));
    setSaved(false);
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;

    // Validate
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file (PNG, JPG, WEBP)");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setError("Image must be under 2 MB");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const supabase = createClient();
      const ext = file.name.split(".").pop() || "png";
      const filePath = `avatars/${user.id}/${Date.now()}.${ext}`;

      // Upload to Supabase storage
      const { error: uploadError } = await supabase.storage
        .from("avatars")
        .upload(filePath, file, { upsert: true });

      if (uploadError) throw uploadError;

      // Get public URL
      const { data: { publicUrl } } = supabase.storage
        .from("avatars")
        .getPublicUrl(filePath);

      // Update user metadata
      const { error: updateError } = await supabase.auth.updateUser({
        data: { avatar_url: publicUrl },
      });
      if (updateError) throw updateError;

      setProfile((p) => ({ ...p, avatar_url: publicUrl }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload avatar");
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const supabase = createClient();
      const { error: updateError } = await supabase.auth.updateUser({
        data: { ...profile },
      });
      if (updateError) throw updateError;
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save profile"
      );
    } finally {
      setSaving(false);
    }
  };

  const initials = profile.full_name
    ? profile.full_name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() ?? "U";

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="animate-reveal">
        <h1 className="text-2xl font-bold tracking-tight text-primary">
          Profile
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Manage your personal information and preferences
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <Card className="animate-reveal d1 h-fit lg:sticky lg:top-20">
          <CardContent className="p-6 text-center">
            {/* Avatar */}
            <div className="relative mx-auto mb-4 group">
              <div className="flex h-24 w-24 mx-auto items-center justify-center rounded-2xl bg-gradient-to-br from-accent/20 via-accent/10 to-accent/5 border border-accent/10 overflow-hidden">
                {profile.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt="Avatar"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-2xl font-bold text-accent">
                    {initials}
                  </span>
                )}
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="absolute left-1/2 -translate-x-1/2 -bottom-1 flex h-8 w-8 items-center justify-center rounded-full bg-accent text-root border-2 border-surface shadow-lg opacity-0 group-hover:opacity-100 transition-all hover:scale-110"
              >
                {uploading ? (
                  <div className="h-3 w-3 rounded-full border-2 border-root border-t-transparent animate-spin" />
                ) : (
                  <Camera className="h-3.5 w-3.5" />
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleAvatarUpload}
                className="hidden"
              />
            </div>

            <h3 className="text-[15px] font-bold text-primary">
              {profile.full_name || "Your Name"}
            </h3>
            {profile.title && (
              <p className="mt-0.5 text-[12px] text-accent font-medium">
                {profile.title}
              </p>
            )}
            <p className="mt-1 text-[12px] text-muted">{user?.email}</p>

            {profile.bio && (
              <p className="mt-3 text-[11px] leading-relaxed text-secondary/70 line-clamp-3">
                {profile.bio}
              </p>
            )}

            {profile.location && (
              <div className="mt-3 inline-flex items-center gap-1.5 text-[11px] text-secondary">
                <MapPin className="h-3 w-3" />
                {profile.location}
              </div>
            )}

            {/* Skills preview */}
            {profile.skills.length > 0 && (
              <div className="mt-4 flex flex-wrap justify-center gap-1.5">
                {profile.skills.slice(0, 8).map((skill) => (
                  <span
                    key={skill}
                    className="rounded-full border border-edge bg-raised/60 px-2.5 py-0.5 text-[10px] font-medium text-secondary"
                  >
                    {skill}
                  </span>
                ))}
                {profile.skills.length > 8 && (
                  <span className="rounded-full border border-edge bg-raised/60 px-2.5 py-0.5 text-[10px] font-medium text-muted">
                    +{profile.skills.length - 8}
                  </span>
                )}
              </div>
            )}

            {/* Social links */}
            {(profile.github_url || profile.linkedin_url) && (
              <div className="mt-4 flex justify-center gap-3">
                {profile.github_url && (
                  <a
                    href={profile.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-edge bg-raised/60 text-secondary hover:text-primary transition"
                  >
                    <Github className="h-4 w-4" />
                  </a>
                )}
                {profile.linkedin_url && (
                  <a
                    href={profile.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-edge bg-raised/60 text-secondary hover:text-primary transition"
                  >
                    <Linkedin className="h-4 w-4" />
                  </a>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="animate-reveal d2">
          <CardContent className="p-6 space-y-5">
            {/* Full Name */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                Full Name
              </label>
              <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 focus-within:border-accent/30 transition">
                <User className="h-4 w-4 shrink-0 text-muted" />
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => handleChange("full_name", e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-transparent text-[13px] text-primary placeholder:text-muted/40 outline-none"
                />
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                Title / Role
              </label>
              <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 focus-within:border-accent/30 transition">
                <Briefcase className="h-4 w-4 shrink-0 text-muted" />
                <input
                  type="text"
                  value={profile.title}
                  onChange={(e) => handleChange("title", e.target.value)}
                  placeholder="Full-Stack Developer"
                  className="w-full bg-transparent text-[13px] text-primary placeholder:text-muted/40 outline-none"
                />
              </div>
            </div>

            {/* Bio */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                Bio
              </label>
              <textarea
                value={profile.bio}
                onChange={(e) => handleChange("bio", e.target.value)}
                placeholder="Tell recruiters about yourself..."
                rows={3}
                className="w-full rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 text-[13px] text-primary placeholder:text-muted/40 outline-none resize-none focus:border-accent/30 transition"
              />
            </div>

            {/* Location */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                Location
              </label>
              <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 focus-within:border-accent/30 transition">
                <MapPin className="h-4 w-4 shrink-0 text-muted" />
                <input
                  type="text"
                  value={profile.location}
                  onChange={(e) => handleChange("location", e.target.value)}
                  placeholder="San Francisco, CA"
                  className="w-full bg-transparent text-[13px] text-primary placeholder:text-muted/40 outline-none"
                />
              </div>
            </div>

            {/* Skills */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                Skills
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addSkill()}
                  placeholder="Add a skill..."
                  className="flex-1 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 text-[13px] text-primary placeholder:text-muted/40 outline-none focus:border-accent/30 transition"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={addSkill}
                  disabled={!newSkill.trim()}
                >
                  <Plus className="h-3.5 w-3.5" />
                </Button>
              </div>
              {profile.skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {profile.skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1 rounded-full border border-edge bg-raised/60 px-2.5 py-1 text-[11px] font-medium text-secondary"
                    >
                      {skill}
                      <button
                        onClick={() => removeSkill(skill)}
                        className="ml-0.5 rounded-full p-0.5 hover:bg-danger/10 hover:text-danger transition"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* GitHub URL */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                GitHub URL
              </label>
              <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 focus-within:border-accent/30 transition">
                <Github className="h-4 w-4 shrink-0 text-muted" />
                <input
                  type="url"
                  value={profile.github_url}
                  onChange={(e) => handleChange("github_url", e.target.value)}
                  placeholder="https://github.com/username"
                  className="w-full bg-transparent text-[13px] text-primary placeholder:text-muted/40 outline-none"
                />
              </div>
            </div>

            {/* LinkedIn URL */}
            <div>
              <label className="mb-1.5 block text-[12px] font-semibold text-secondary">
                LinkedIn URL
              </label>
              <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-root/60 px-3.5 py-2.5 focus-within:border-accent/30 transition">
                <Linkedin className="h-4 w-4 shrink-0 text-muted" />
                <input
                  type="url"
                  value={profile.linkedin_url}
                  onChange={(e) =>
                    handleChange("linkedin_url", e.target.value)
                  }
                  placeholder="https://linkedin.com/in/username"
                  className="w-full bg-transparent text-[13px] text-primary placeholder:text-muted/40 outline-none"
                />
              </div>
            </div>

            {/* Error / Success */}
            {error && (
              <p className="rounded-lg bg-danger/10 border border-danger/20 px-4 py-2 text-[12px] text-danger">
                {error}
              </p>
            )}

            {/* Save */}
            <div className="flex justify-end pt-2">
              <Button onClick={handleSave} disabled={saving} className="gap-2">
                {saving ? (
                  <div className="h-3.5 w-3.5 rounded-full border-2 border-root border-t-transparent animate-spin" />
                ) : saved ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                {saving ? "Saving..." : saved ? "Saved" : "Save Profile"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
