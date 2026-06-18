import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
  Outlet,
} from "@tanstack/react-router";
import { DatasetDetailPage } from "@/pages/DatasetDetail";
import { DatasetLineagePage } from "@/pages/DatasetLineage";
import { DatasetsPage } from "@/pages/Datasets";
import { LineagePage } from "@/pages/Lineage";
import { ObjectTypeDetailPage } from "@/pages/ObjectTypeDetail";
import { OntologyPage } from "@/pages/Ontology";
import { DashboardBuilderPage } from "@/pages/DashboardBuilder";
import { DashboardViewerPage } from "@/pages/DashboardViewer";
import { WorkshopPage } from "@/pages/Workshop";
import { PipelineBuilderPage } from "@/pages/PipelineBuilder";
import { PipelineDetailPage } from "@/pages/PipelineDetail";
import { PipelinesPage } from "@/pages/Pipelines";
import { SourceDetailPage } from "@/pages/SourceDetail";
import { SourcesPage } from "@/pages/Sources";

const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Navigate to="/sources" />,
});

const sourcesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/sources",
  component: SourcesPage,
});

const sourceDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/sources/$id",
  component: function SourceDetailRoute() {
    const { id } = sourceDetailRoute.useParams();
    return <SourceDetailPage id={id} />;
  },
});

const datasetsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/datasets",
  component: DatasetsPage,
});

const datasetDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/datasets/$id",
  component: function DatasetDetailRoute() {
    const { id } = datasetDetailRoute.useParams();
    return <DatasetDetailPage id={id} />;
  },
});

const pipelinesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/pipelines",
  component: PipelinesPage,
});

const pipelineDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/pipelines/$id",
  component: function PipelineDetailRoute() {
    const { id } = pipelineDetailRoute.useParams();
    return <PipelineDetailPage id={id} />;
  },
});

const pipelineBuilderRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/pipelines/$id/builder",
  component: function PipelineBuilderRoute() {
    const { id } = pipelineBuilderRoute.useParams();
    return <PipelineBuilderPage id={id} />;
  },
});

const lineageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/lineage",
  component: LineagePage,
});

const datasetLineageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/lineage/dataset/$id",
  component: function DatasetLineageRoute() {
    const { id } = datasetLineageRoute.useParams();
    return <DatasetLineagePage id={id} />;
  },
});

const ontologyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ontology",
  component: OntologyPage,
});

const objectTypeDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ontology/types/$id",
  component: function ObjectTypeDetailRoute() {
    const { id } = objectTypeDetailRoute.useParams();
    return <ObjectTypeDetailPage id={id} />;
  },
});

const workshopRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workshop",
  component: WorkshopPage,
});

const dashboardBuilderRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workshop/$id/edit",
  component: function DashboardBuilderRoute() {
    const { id } = dashboardBuilderRoute.useParams();
    return <DashboardBuilderPage id={id} />;
  },
});

const dashboardViewerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workshop/$id/view",
  component: function DashboardViewerRoute() {
    const { id } = dashboardViewerRoute.useParams();
    return <DashboardViewerPage id={id} />;
  },
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  sourcesRoute,
  sourceDetailRoute,
  datasetsRoute,
  datasetDetailRoute,
  pipelinesRoute,
  pipelineDetailRoute,
  pipelineBuilderRoute,
  lineageRoute,
  datasetLineageRoute,
  ontologyRoute,
  objectTypeDetailRoute,
  workshopRoute,
  dashboardBuilderRoute,
  dashboardViewerRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
