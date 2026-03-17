from typing import List, Dict, Any, Optional
import uuid
from repositories.review_repository import ReviewRepository
from repositories.worker_repository import WorkerRepository

class ReviewService:
    _review_repo = ReviewRepository()
    _worker_repo = WorkerRepository()

    @staticmethod
    async def leave_review(worker_id: str, customer_id: str, rating: int, comment: Optional[str]) -> Dict[str, Any]:
        data = {
            "id": str(uuid.uuid4()),
            "worker_id": worker_id,
            "customer_id": customer_id,
            "rating": rating,
            "comment": comment
        }
        review = await ReviewService._review_repo.insert(data)
        
        # Update worker average rating
        avg_rating = await ReviewService._review_repo.get_average_rating(worker_id)
        await ReviewService._worker_repo.update(worker_id, {"rating": avg_rating})
        
        return review

    @staticmethod
    async def list_worker_reviews(worker_id: str) -> List[Dict[str, Any]]:
        return await ReviewService._review_repo.list_by_worker(worker_id)

    @staticmethod
    async def get_worker_rating_stats(worker_id: str) -> Dict[str, Any]:
        """
        Calculates rating distribution and average.
        """
        reviews = await ReviewService._review_repo.list_by_worker(worker_id)
        if not reviews:
            return {"average": 0.0, "total": 0, "distribution": {i: 0 for i in range(1, 6)}}
        
        distribution = {i: 0 for i in range(1, 6)}
        total_rating = 0
        for r in reviews:
            rating = r.get("rating", 0)
            if 1 <= rating <= 5:
                distribution[rating] += 1
                total_rating += rating
        
        return {
            "average": round(total_rating / len(reviews), 2),
            "total": len(reviews),
            "distribution": distribution
        }
