 "use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { getProfile, validateProfile, updateProfile, type Profile, type ProfileValidation } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle, XCircle, ShieldCheck, Edit, Save } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [validation, setValidation] = useState<ProfileValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<Partial<Profile>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await getProfile();
        setProfile(p);
      } catch (e) {
        toast.error(`Failed to load profile: ${(e as Error).message}`);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleValidate = async () => {
    setValidating(true);
    setValidation(null);
    try {
      const result = await validateProfile();
      setValidation(result);
      if (result.valid) {
        toast.success("Profile is valid.");
      } else {
        toast.warning("Profile has validation errors.");
      }
    } catch (e) {
      toast.error(`Validation failed: ${(e as Error).message}`);
    } finally {
      setValidating(false);
    }
  };

  const handleEditClick = () => {
    setFormData(profile || {});
    setIsEditing(true);
  };

  const handeSave = async () => {
    setSaving(true);
    try {
      const updated = await updateProfile(formData);
      setProfile(updated);
      setIsEditing(false);
      toast.success("Profile updated successfully.");
      // Auto-validate after update
      handleValidate();
    } catch (e) {
      toast.error(`Failed to update profile: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar
        title="Profile"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleEditClick}>
              <Edit className="h-4 w-4 mr-1" />
              Edit Profile
            </Button>
            <Button size="sm" onClick={handleValidate} disabled={validating}>
              <ShieldCheck className="h-4 w-4 mr-1" />
              {validating ? "Validating..." : "Validate"}
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Validation result */}
          {validation && (
            <Card className={validation.valid ? "border-green-500" : "border-red-500"}>
              <CardContent className="py-4">
                {validation.valid ? (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Profile is valid</span>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-red-600">
                      <XCircle className="h-5 w-5" />
                      <span className="font-medium">Validation failed</span>
                    </div>
                    <ul className="ml-7 space-y-1">
                      {(validation.errors ?? []).map((err, i) => (
                        <li key={i} className="text-sm text-red-600">{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Profile data */}
          <Card>
            <CardHeader>
              <CardTitle>Profile Details</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-6 w-full" />
                  ))}
                </div>
              ) : !profile ? (
                <p className="text-muted-foreground">No profile data available.</p>
              ) : (
                <div className="divide-y">
                  {Object.entries(profile).map(([key, value]) => (
                    <div key={key} className="py-3 grid grid-cols-3 gap-4">
                      <span className="text-sm font-medium text-muted-foreground capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <div className="col-span-2">
                        {Array.isArray(value) ? (
                          <div className="flex flex-wrap gap-1">
                            {(value as string[]).map((v, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">{v}</Badge>
                            ))}
                          </div>
                        ) : typeof value === "object" && value !== null ? (
                          <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-40">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        ) : (
                          <span className="text-sm">{renderValue(value)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4">
            {/* Column 1: Personal Info */}
            <div className="space-y-4">
              <h3 className="font-semibold text-sm border-b pb-1">Personal Information</h3>
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" value={String(formData.name || "")} onChange={(e) => handleChange("name", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" value={String(formData.email || "")} onChange={(e) => handleChange("email", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" value={String(formData.phone || "")} onChange={(e) => handleChange("phone", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input id="location" value={String(formData.location || "")} onChange={(e) => handleChange("location", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="linkedin">LinkedIn</Label>
                <Input id="linkedin" value={String(formData.linkedin || "")} onChange={(e) => handleChange("linkedin", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="github">GitHub</Label>
                <Input id="github" value={String(formData.github || "")} onChange={(e) => handleChange("github", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="portfolio">Portfolio</Label>
                <Input id="portfolio" value={String(formData.portfolio || "")} onChange={(e) => handleChange("portfolio", e.target.value)} />
              </div>
            </div>

            {/* Column 2: Content Sections */}
            <div className="space-y-4">
              <h3 className="font-semibold text-sm border-b pb-1">Professional Content</h3>
              <div className="space-y-2">
                <Label htmlFor="summary">Summary</Label>
                <Textarea id="summary" className="h-24" value={String(formData.summary || "")} onChange={(e) => handleChange("summary", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="skills">Skills</Label>
                <Textarea id="skills" className="h-24" value={String(formData.skills || "")} onChange={(e) => handleChange("skills", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="experience">Experience</Label>
                <Textarea id="experience" className="h-32" value={String(formData.experience || "")} onChange={(e) => handleChange("experience", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="education">Education</Label>
                <Textarea id="education" className="h-24" value={String(formData.education || "")} onChange={(e) => handleChange("education", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="achievements">Achievements</Label>
                <Textarea id="achievements" className="h-24" value={String(formData.achievements || "")} onChange={(e) => handleChange("achievements", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="certifications">Certifications</Label>
                <Textarea id="certifications" className="h-24" value={String(formData.certifications || "")} onChange={(e) => handleChange("certifications", e.target.value)} />
              </div>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="ghost">Cancel</Button>
            </DialogClose>
            <Button onClick={handeSave} disabled={saving}>
              <Save className="h-4 w-4 mr-1" />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
