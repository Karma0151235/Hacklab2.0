import { Skeleton } from "@/components/ui/skeleton"

export default function CompaniesLoading() {
  return (
    <div className="container mx-auto p-6 space-y-8 max-w-7xl">
       {/* Header */}
       <div className="flex items-center justify-between gap-4">
         <div className="space-y-2">
            <Skeleton className="h-9 w-48" />
            <Skeleton className="h-4 w-64" />
         </div>
         <Skeleton className="h-10 w-32" />
       </div>

       {/* Toolbar */}
       <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-between">
            <Skeleton className="h-10 w-full sm:w-[300px]" />
            <div className="flex gap-2">
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
            </div>
          </div>

          {/* Table Skeleton */}
          <div className="rounded-md border border-slate-800 bg-slate-950/50">
            <div className="p-4 border-b border-slate-800 flex gap-4">
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-[200px]" />
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-[50px] ml-auto" />
            </div>
            {[1,2,3,4,5,6].map(i => (
              <div key={i} className="p-4 border-b border-slate-800 last:border-0 flex items-center gap-4">
                 <Skeleton className="h-4 w-[100px]" />
                 <div className="flex items-center gap-2 flex-1">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <Skeleton className="h-4 w-[150px]" />
                 </div>
                 <Skeleton className="h-6 w-[80px] rounded-full" />
                 <Skeleton className="h-4 w-[80px]" />
                 <Skeleton className="h-8 w-8 rounded-md ml-auto" />
              </div>
            ))}
          </div>
       </div>
    </div>
  )
}
