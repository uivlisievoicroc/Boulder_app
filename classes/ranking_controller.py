# ranking_controller.py

class RankingController:
    def __init__(self, route_scores, competitors, routes):
        self.route_scores = route_scores
        self.competitors = competitors
        self.routes = routes

    def calculate_total(self, competitor):
        return sum(
            self.route_scores[competitor].get(r, 0)
            if isinstance(self.route_scores[competitor].get(r, 0), (int, float))
            else 0
            for r in self.routes
        )

    def generate_ranked_list(self):
        return sorted(
            self.competitors,
            key=lambda c: self.calculate_total(c),
            reverse=True
        )