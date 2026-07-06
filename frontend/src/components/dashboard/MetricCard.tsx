import type { Metric } from "@/data/dashboardData";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type MetricCardProps = {
  metric: Metric;
};

export function MetricCard({ metric }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-muted-foreground">{metric.label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-3xl font-semibold tracking-normal">{metric.value}</p>
        <div>
          <p className="text-sm text-muted-foreground">{metric.detail}</p>
          <p className="mt-1 text-xs font-medium text-primary">{metric.trend}</p>
        </div>
      </CardContent>
    </Card>
  );
}
