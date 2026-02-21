import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface SelectionCardProps {
    title: string;
    description?: string;
    icon?: React.ReactNode;
    selected?: boolean;
    onClick?: () => void;
    imageSrc?: string;
}

export function SelectionCard({ title, description, icon, selected, onClick, imageSrc }: SelectionCardProps) {
    return (
        <div
            onClick={onClick}
            className={cn(
                "relative group cursor-pointer rounded-xl border-2 p-4 transition-all hover:border-primary/50 hover:bg-accent",
                selected ? "border-primary bg-accent/50" : "border-muted bg-card"
            )}
        >
            {selected && (
                <div className="absolute top-2 right-2 text-primary">
                    <Check className="h-5 w-5" />
                </div>
            )}

            <div className="flex flex-col items-center text-center space-y-4">
                {imageSrc ? (
                    <div className="relative w-full aspect-video rounded-lg overflow-hidden mb-2">
                        {/* Use simple img for now, in real app use Next.js Image */}
                        <img src={imageSrc} alt={title} className="object-cover w-full h-full" />
                    </div>
                ) : icon ? (
                    <div className={cn("p-4 rounded-full bg-secondary transition-colors group-hover:bg-background", selected && "bg-background text-primary")}>
                        {icon}
                    </div>
                ) : null}

                <div className="space-y-1">
                    <h3 className="font-semibold">{title}</h3>
                    {description && <p className="text-sm text-muted-foreground">{description}</p>}
                </div>
            </div>
        </div>
    );
}
