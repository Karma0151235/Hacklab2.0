"use client"

import * as React from "react"
import { Monitor, Bell, Key, User, Shield, Moon, Sun, Laptop, Save, LogOut } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAppStore } from "@/stores/use-app-store"
import { toast } from "sonner"

export default function SettingsPage() {
  const { theme, setTheme } = useAppStore()
  const [isLoading, setIsLoading] = React.useState(false)

  const handleSave = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      toast.success("Settings saved successfully")
    }, 1000)
  }

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-5xl animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Settings</h1>
        <p className="text-slate-400 mt-2">
          Manage your account settings and preferences.
        </p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="bg-slate-900 border border-slate-800">
          <TabsTrigger value="general" className="data-[state=active]:bg-cyan-500 data-[state=active]:text-slate-950">General</TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-cyan-500 data-[state=active]:text-slate-950">Notifications</TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-cyan-500 data-[state=active]:text-slate-950">Security</TabsTrigger>
        </TabsList>

        <div className="mt-6">
          {/* General Settings */}
          <TabsContent value="general" className="space-y-6">
            
            {/* Appearance */}
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5 text-cyan-400" />
                  Appearance
                </CardTitle>
                <CardDescription>
                  Customize the look and feel of the application.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Theme Mode</Label>
                    <p className="text-sm text-slate-500">
                      Select your preferred theme.
                    </p>
                  </div>
                  <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setTheme('light')}
                      className={theme === 'light' ? 'bg-slate-800 text-slate-100' : 'text-slate-500'}
                    >
                      <Sun className="h-4 w-4 mr-2" /> Light
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setTheme('dark')}
                      className={theme === 'dark' ? 'bg-slate-800 text-slate-100' : 'text-slate-500'}
                    >
                      <Moon className="h-4 w-4 mr-2" /> Dark
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Profile */}
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5 text-cyan-400" />
                  Profile
                </CardTitle>
                <CardDescription>
                  Manage your public profile information.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                    <Avatar className="h-16 w-16">
                      <AvatarImage src="/avatars/01.png" alt="@johndoe" />
                      <AvatarFallback>JD</AvatarFallback>
                    </Avatar>
                    <Button variant="outline">Change Avatar</Button>
                </div>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      Name
                    </Label>
                    <Input id="name" defaultValue="John Doe" className="col-span-3" />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="email" className="text-right">
                      Email
                    </Label>
                    <Input id="email" defaultValue="john.doe@ambank.com" className="col-span-3" />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-slate-800 pt-4">
                 <Button onClick={handleSave} disabled={isLoading}>
                    {isLoading ? "Saving..." : "Save Changes"}
                 </Button>
              </CardFooter>
            </Card>

          </TabsContent>

          {/* Notifications Settings */}
          <TabsContent value="notifications" className="space-y-6">
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-cyan-400" />
                  Alert Preferences
                </CardTitle>
                <CardDescription>
                  Choose how and when you want to be notified.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label className="text-base">Real-time Alerts</Label>
                    <p className="text-sm text-slate-500">
                      Receive toast notifications when new alerts are triggered.
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Separator className="bg-slate-800" />
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label className="text-base">Email Digest</Label>
                    <p className="text-sm text-slate-500">
                      Receive a daily summary of high-severity alerts.
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Separator className="bg-slate-800" />
                <div className="flex items-center justify-between space-x-2">
                  <div className="space-y-0.5">
                    <Label className="text-base">Scraping Jobs</Label>
                    <p className="text-sm text-slate-500">
                      Notify me when a large scraping job completes.
                    </p>
                  </div>
                  <Switch />
                </div>

              </CardContent>
              <CardFooter className="justify-end border-t border-slate-800 pt-4">
                 <Button onClick={handleSave} disabled={isLoading}>
                    {isLoading ? "Saving..." : "Save Changes"}
                 </Button>
              </CardFooter>
            </Card>
          </TabsContent>

          {/* Security Settings */}
          <TabsContent value="security" className="space-y-6">
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-cyan-400" />
                  API Access
                </CardTitle>
                <CardDescription>
                  Manage API keys for external integrations.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                   <Label>OpenAI API Key</Label>
                   <div className="flex gap-2">
                     <Input type="password" value="sk-........................" readOnly className="font-mono text-slate-500" />
                     <Button variant="outline">Update</Button>
                   </div>
                </div>
              </CardContent>
            </Card>

             <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader>
                <CardTitle className="text-red-400">Danger Zone</CardTitle>
                <CardDescription>
                  Irreversible actions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                 <Button variant="destructive" className="w-full sm:w-auto">
                   <LogOut className="mr-2 h-4 w-4" /> Sign Out
                 </Button>
              </CardContent>
             </Card>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
